"""PhysiLearn 2.0: deterministic motion summary and formula cards.

Only uses saved experiment measurements (no webcam frames, API key or network).
The event detector is heuristic, so descriptions must remain approximate.
"""
from __future__ import annotations

import math
from statistics import median


def _number(value):
    try:
        v = float(value)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError, OverflowError):
        return None


def _nice(v, digits=2):
    if v is None:
        return "N/A"
    return f"{v:,.{digits}f}"


def _moving_median(vals, radius=3):
    return [median(vals[max(0, i-radius):min(len(vals), i+radius+1)])
            for i in range(len(vals))]


def _percentile(vals, pct):
    if not vals:
        return 0.0
    v = sorted(vals)
    pos = max(0.0, min(1.0, pct)) * (len(v)-1)
    lo = int(pos)
    hi = min(len(v)-1, lo+1)
    return v[lo] + (v[hi]-v[lo]) * (pos-lo)


def _valid_samples(lab, result):
    raw = result.get("samples")
    # PHYSILEARN_RAMP_SEGMENTS_SAFE_V1
    # For interrupted ramp recordings, do not infer speed across missing frames.
    # Analyze the longest uninterrupted segment rather than joining the gaps.
    if lab == "ramp" and result.get("tracking_gaps", 0) and isinstance(raw, list):
        groups = {}
        for sample in raw:
            if isinstance(sample, dict):
                groups.setdefault(sample.get("segment_id", 0), []).append(sample)
        if groups:
            raw = max(groups.values(), key=lambda group: (
                (group[-1].get("time_s", 0) - group[0].get("time_s", 0))
                if len(group) > 1 else 0
            ))
    if not isinstance(raw, list):
        return [], [], ""
    samples = []
    for s in raw[:12000]:
        if not isinstance(s, dict):
            continue
        t = _number(s.get("time_s"))
        pos = _number(s.get("cumulative_distance_px" if lab == "object" else "along_ramp_px"))
        if t is None or pos is None or (samples and t <= samples[-1][0]):
            continue
        samples.append((t, pos))
    if len(samples) < 10 or samples[-1][0] - samples[0][0] < 0.5:
        return [], [], ""
    t0 = samples[0][0]
    times = [t - t0 for t, _ in samples]
    p = [pos for _, pos in samples]
    unit = "cm" if lab == "object" and result.get("measurement_units") == "cm" else "px"
    if unit == "cm":
        scale = _number(result.get("pixels_per_cm"))
        if not scale or scale <= 0:
            unit = "px"
        else:
            p = [x / scale for x in p]
    return times, p, unit


def _window_velocities(times, positions, lab, window_s=0.40):
    # Windowed deltas suppress frame-to-frame noise; signed for ramp, unsigned for object.
    velocities = []
    start = 0
    for i, t in enumerate(times):
        while start < i and t - times[start] > window_s:
            start += 1
        k = max(0, start-1)
        dt = t-times[k]
        v = (positions[i]-positions[k])/dt if dt >= 0.08 else 0.0
        velocities.append(max(0.0, v) if lab == "object" else v)
    return _moving_median(velocities, radius=3)


def _windows_from_flags(times, active, max_gap_s=0.20, min_duration_s=0.20):
    # Merge brief low-speed gaps; ignore isolated single-frame tracking noise.
    inds = [i for i, yes in enumerate(active) if yes]
    if not inds:
        return []
    runs = []
    start = prev = inds[0]
    for i in inds[1:]:
        if times[i]-times[prev] <= max_gap_s:
            prev = i
        else:
            if times[prev]-times[start] >= min_duration_s:
                runs.append((start, prev))
            start = prev = i
    if times[prev]-times[start] >= min_duration_s:
        runs.append((start, prev))
    return runs


def build_motion_report(lab, result):
    """Return user-facing segments and bounded numeric facts for the AI."""
    times, p, unit = _valid_samples(lab, result)
    if not times:
        return {
            "summary": "Not enough timestamped tracking samples to analyze individual motion intervals.",
            "segments": [], "confidence_note": "Use the numerical results above; timed motion analysis is unavailable.",
            "ai_facts": {"available": False, "reason": "missing or insufficient time series"},
        }

    velocities = _window_velocities(times, p, lab)
    magnitudes = [abs(x) for x in velocities]
    # Absolute threshold plus robust percentile: avoid treating subpixel jitter as motion.
    # Pixel speed is not a measured physical speed in meters/second.
    threshold = max(10.0 if unit == "px" else 0.75, 0.12*_percentile(magnitudes, .90))
    active = [v >= threshold for v in magnitudes]
    runs = _windows_from_flags(times, active)
    peak = max(magnitudes)
    observation_time = times[-1]
    detected_time = sum(times[b]-times[a] for a, b in runs)
    summary = (f"Detected {len(runs)} approximate motion interval(s) within "
               f"{observation_time:.2f} s of recording. "
               f"Intervals are based on estimated {unit}/s speeds, not direct force measurements.")

    segments = []
    for i, (a, b) in enumerate(runs[:5], start=1):
        snippet = velocities[a:b+1]
        maxima = max(abs(v) for v in snippet)
        label = "Moving (estimated)"
        description = (f"Motion detected; estimated peak window speed near "
                       f"{_nice(maxima, 1)} {unit}/s.")
        # Describe observed trends in the windowed speed estimate, not
        # trustworthy force/acceleration. Require a broad increase and decrease
        # so a one-frame spike does not automatically count as a phase.
        peak_idx = a + max(range(len(snippet)), key=lambda j: abs(snippet[j]))
        if (times[b]-times[a] >= 0.60 and times[peak_idx]-times[a] >= 0.18
                and times[b]-times[peak_idx] >= 0.18
                and abs(velocities[peak_idx]) > 1.6*max(abs(velocities[a]), 1.0)
                and abs(velocities[peak_idx]) > 1.6*max(abs(velocities[b]), 1.0)):
            description += (f" Estimated speed rose from ~{times[a]:.2f} to "
                            f"{times[peak_idx]:.2f} s and then decreased "
                            f"toward ~{times[b]:.2f} s; exact acceleration "
                            "is not established.")
        if lab == "ramp":
            mean_signed = sum(snippet)/len(snippet)
            if mean_signed < -threshold:
                description += " Motion mostly opposite the marked downhill axis."
            elif mean_signed > threshold:
                description += " Motion mostly in the marked downhill direction."
        segments.append({
            "label": f"Interval {i} · {label}",
            "time": f"{times[a]:.2f}–{times[b]:.2f} s",
            "description": description,
            "start_s": round(times[a], 2),
            "end_s": round(times[b], 2),
            "peak_estimate": round(maxima, 1),
        })
    if not runs:
        summary = "No sustained motion intervals cleared the tracking-noise threshold. Try a longer, steadier recording."
    note = ("Motion times and peak window speeds are approximate. Sudden peaks or gaps may "
            "come from tracking noise, occlusion, perspective or a real change in motion. "
            "The detector cannot establish acceleration or its cause reliably.")
    ai_facts = {
        "available": True,
        "recording_span_s": round(observation_time, 2),
        "detected_motion_intervals": len(runs),
        "motion_windows": [{"from_s": x["start_s"], "to_s": x["end_s"],
                            "peak_window_speed": x["peak_estimate"]} for x in segments],
        "speed_unit": unit + "/s",
        "noise_floor_threshold": round(threshold, 2),
        "note": "Approximate detector, not verified acceleration or force. Peaks may be noise.",
    }
    if lab == "ramp" and result.get("tracking_gaps", 0):
        note += " Tracking was interrupted; only the longest uninterrupted segment was analyzed."
        ai_facts["tracking_interrupted"] = True
        ai_facts["interpretation_limit"] = "Only the longest continuous tracked segment; never bridge occluded time."
    return {"summary": summary, "segments": segments,
            "confidence_note": note, "ai_facts": ai_facts}


def build_formula_cards(lab, result):
    """Use saved rounded summary fields; do not invent physical SI calibration."""
    time = _number(result.get("duration_s"))
    if time is None or time <= 0:
        return []
    # Recording summaries are rounded, while timestamps retain more precision.
    # Prefer the actual frame span when it closely matches the reported time.
    raw = result.get("samples")
    if isinstance(raw, list) and len(raw) >= 2:
        a = _number(raw[0].get("time_s")) if isinstance(raw[0], dict) else None
        b = _number(raw[-1].get("time_s")) if isinstance(raw[-1], dict) else None
        if a is not None and b is not None and b > a and abs((b-a)-time) < max(0.10, time*0.03):
            time = b-a
    cards = []
    if lab == "object":
        unit = result.get("measurement_units") if result.get("measurement_units") in ("cm", "px") else "px"
        distance = _number(result.get("distance"))
        displacement = _number(result.get("displacement_magnitude"))
        if distance is not None and distance >= 0:
            avg = distance/time
            cards.append({
                "title": "AVERAGE SPEED", "formula": "Average speed = s / Δt",
                "substitution": f"{_nice(distance)} {unit} / {_nice(time, 3)} s ≈ {_nice(avg)} {unit}/s",
                "explanation": "Here s is the total tracked path and Δt is the recording duration. This includes any stationary time, so it is not peak speed.",
                "ai_fact": {"quantity": "average_speed", "value": round(avg, 2), "unit": unit + "/s"},
            })
        if displacement is not None and displacement >= 0:
            magnitude = displacement/time
            cards.append({
                "title": "MAGNITUDE OF AVERAGE VELOCITY", "formula": "Average velocity magnitude = |Δr| / Δt",
                "substitution": f"{_nice(displacement)} {unit} / {_nice(time, 3)} s ≈ {_nice(magnitude)} {unit}/s",
                "explanation": "Here |Δr| is the straight-line displacement magnitude from start to finish; it does not include the whole route. Direction is not shown.",
                "ai_fact": {"quantity": "average_velocity_magnitude", "value": round(magnitude, 2), "unit": unit + "/s"},
            })
        if distance and displacement is not None:
            raw_ratio = 100 * displacement / distance
            inconsistent = displacement > distance + max(0.1, 0.002 * distance)
            ratio = max(0.0, min(100.0, raw_ratio)) if not inconsistent else raw_ratio
            detail = (
                "Measurement inconsistency: displacement exceeds total path, which is not physically possible "
                "for exact measurements. Tracking or rounding errors may be responsible. Do not interpret "
                "this ratio as verified straight-line motion."
                if inconsistent else
                "Near 100% suggests a mostly direct path; a lower ratio suggests detours or reversals. "
                "This ratio is not a new speed."
            )
            cards.append({
                "title": "PATH DIRECTNESS" + (" · CHECK MEASUREMENT" if inconsistent else ""),
                "formula": "Directness = |Δr| / s × 100%",
                "substitution": f"{_nice(displacement)} / {_nice(distance)} × 100% ≈ {_nice(ratio, 1)}%",
                "explanation": detail,
                "ai_fact": {"quantity": "displacement_distance_ratio_pct", "value": round(ratio, 1),
                            "unit": "%", "measurement_consistent": not inconsistent,
                            "warning": detail if inconsistent else None},
            })
    else:
        unit = "px"
        path = _number(result.get("approx_along_ramp_path_px"))
        displacement = _number(result.get("along_ramp_displacement_px"))
        if path is not None and path >= 0:
            cards.append({
                "title": "AVERAGE PATH SPEED", "formula": "Average speed ≈ s(ramp) / Δt",
                "substitution": f"{_nice(path)} {unit} / {_nice(time, 3)} s ≈ {_nice(path/time)} {unit}/s",
                "explanation": "Estimated path includes tracker jitter and stationary recording time.",
                "ai_fact": {"quantity": "average_path_speed_estimate", "value": round(path/time, 2), "unit": "px/s"},
            })
        if displacement is not None:
            cards.append({
                "title": "AVERAGE ALONG-RAMP VELOCITY", "formula": "Average velocity = Δr(ramp) / Δt",
                "substitution": f"{_nice(displacement)} {unit} / {_nice(time, 3)} s ≈ {_nice(displacement/time)} {unit}/s",
                "explanation": "Positive means the marked downhill direction; negative means uphill. Not peak velocity.",
                "ai_fact": {"quantity": "average_along_ramp_velocity", "value": round(displacement/time, 2), "unit": "px/s"},
            })
        cards.append({
            "title": "ACCELERATION (CONCEPT)", "formula": "Average acceleration = Δv / Δt",
            "substitution": "Not calculated: reliable start/end velocities were not measured.",
            "explanation": "Steeper ramps can change acceleration, but these webcam samples cannot establish a numeric acceleration reliably.",
            "ai_fact": {"quantity": "acceleration", "value": None, "unit": "unavailable"},
        })
    return cards
