"""PhysiLearn: evidence-based four-part AI motion explanation.

Uses saved numerical summaries, never video frames. Designed to coexist with the
existing Physics Tutor quick summary, Motion Analysis, and Formula Explorer.
"""
from __future__ import annotations

import json
import math
import os
import re
from pathlib import Path

HEADINGS = (
    "HOW IT MOVED",
    "WHY IT CHANGED",
    "PHYSICS BEHIND IT",
    "WHAT WE LEARNED",
)


def _number(x):
    try:
        value = float(x)
        return value if math.isfinite(value) else None
    except (TypeError, ValueError, OverflowError):
        return None


def _n(value, places=2):
    return f"{value:.{places}f}" if value is not None else "unavailable"


def _unit(lab, result):
    return ("cm" if result.get("measurement_units") == "cm" else "px") if lab == "object" else "px"


def _measurement_warning(lab, result):
    if lab == "object":
        d = _number(result.get("distance"))
        delta = _number(result.get("displacement_magnitude"))
        if d is not None and delta is not None and delta > d + max(.1, .002*d):
            return ("Recorded displacement is larger than tracked distance. This is not physically "
                    "consistent and signals tracking/calculation error. Do not infer straight motion "
                    "or compute a valid directness ratio from these values.")
        gaps = _number(result.get("tracking_gap_count"))
        if gaps is not None and gaps > 0:
            return (f"Tracking was interrupted {int(gaps)} time(s). Motion during interruptions "
                    "was not measured; the path may be underestimated.")
    return "Tracker noise, perspective and occlusion may distort short speed peaks."


def story_facts(lab, result):
    """Compact, verifiable input for the model: never include raw frames or secret fields."""
    from eureka_motion_analysis import build_motion_report, build_formula_cards

    motion = build_motion_report(lab, result)
    formula_cards = build_formula_cards(lab, result)
    unit = _unit(lab, result)
    facts = {
        "lab": "Object Physics Lab" if lab == "object" else "Ramp Physics Lab",
        "object_name": str(result.get("object_name", "Object"))[:80] if lab == "object" else "Object on inclined plane",
        "distance_unit": unit,
        "duration_s": _number(result.get("duration_s")),
        "ruler_calibrated": bool(result.get("calibration_used")) if lab == "object" else False,
        "motion_intervals_detector": motion.get("ai_facts", {}),
        "motion_segment_descriptions": [
            {"time": s.get("time", ""), "description": s.get("description", "")}
            for s in motion.get("segments", [])[:5]
        ],
        "formula_results": [c.get("ai_fact", {}) for c in formula_cards],
        "measurement_warning": _measurement_warning(lab, result),
    }
    if lab == "object":
        facts.update({
            "tracked_distance": _number(result.get("distance")),
            "displacement_magnitude": _number(result.get("displacement_magnitude")),
            "recorded_average_speed": _number(result.get("average_speed")),
            "tracking_gap_count": _number(result.get("tracking_gap_count")),
        })
    else:
        facts.update({
            "estimated_along_ramp_path_px": _number(result.get("approx_along_ramp_path_px")),
            "along_ramp_displacement_px": _number(result.get("along_ramp_displacement_px")),
            "estimated_peak_downhill_velocity_px_s": _number(result.get("peak_downhill_velocity_px_s")),
        })
    return facts


def parse_story_sections(message):
    """Accept plain text, markdown headings and e.g. '01 · HOW IT MOVED'."""
    collected = {key: [] for key in HEADINGS}
    selected = None
    for raw in str(message).splitlines():
        line = raw.strip()
        if not line:
            continue
        cleaned = re.sub(r"^#{1,6}\s*", "", line)
        cleaned = re.sub(r"^\d{1,2}\s*[.)·:-]\s*", "", cleaned)
        cleaned = cleaned.strip(" *_`#—- ")
        maybe_heading, colon, tail = cleaned.partition(":")
        label = maybe_heading.strip(" *_`#—- ").upper()
        if label in collected:
            selected = label
            if colon and tail.strip():
                collected[label].append(tail.strip(" *_`"))
        elif selected is not None:
            collected[selected].append(line)
    return {key: " ".join(chunks).strip() for key, chunks in collected.items()}


def _as_text(parts):
    return "\n\n".join(f"{name}\n{parts[name]}" for name in HEADINGS)


def local_story_explanation(lab, result):
    """Useful offline response that does not fabricate velocity changes/causes."""
    from eureka_motion_analysis import build_motion_report

    report = build_motion_report(lab, result)
    ai_facts = report.get("ai_facts", {})
    count = ai_facts.get("detected_motion_intervals") if ai_facts.get("available") else None
    unit = _unit(lab, result)
    duration = _number(result.get("duration_s"))
    recorded_time = f" during {_n(duration)} s" if duration is not None else ""
    windows = ai_facts.get("motion_windows", [])
    observed_windows = (" Detected windows: " + ", ".join(
        f"{w.get('from_s', '?')}–{w.get('to_s', '?')} s" for w in windows[:3]) + ".") if windows else ""
    if lab == "object":
        name = str(result.get("object_name", "The tracked object"))[:80]
        d = _number(result.get("distance"))
        delta = _number(result.get("displacement_magnitude"))
        speed = _number(result.get("average_speed"))
        first = (f"{name} covered about {_n(d)} {unit}{recorded_time}. "
                 f"Start-to-finish displacement magnitude was {_n(delta)} {unit}.")
        if count is not None:
            first += f" The detector found {count} approximate moving interval(s)." + observed_windows
        else:
            first += " There is not enough reliable time-series data to describe the motion phases."
        note = _measurement_warning(lab, result)
        why = ("Estimated speed may rise or fall as the object starts, slows, or changes its motion. "
               "A push, friction, or a change in direction could contribute, but the webcam alone "
               "cannot prove any particular cause. " + note)
        physics = (f"Average speed is total tracked distance divided by recording time"
                   + (f": {_n(d)} {unit} / {_n(duration)} s ≈ {_n(speed)} {unit}/s. "
                      if d is not None and duration and duration > 0 else ". ")
                   + "A return trip can reduce net displacement while increasing distance traveled; "
                   "returning does not by itself lower average speed. This is not an instantaneous speed.")
        takeaway = ("Repeat a steady one-way trial, then a forward-and-back trial with the "
                    "same setup. Compare distance, displacement and speed; keep the camera "
                    "still and check that tracking stays on the object.")
    else:
        displacement = _number(result.get("along_ramp_displacement_px"))
        first = (f"The object changed its position along the marked ramp by about "
                 f"{_n(displacement)} px{recorded_time}.")
        if count is not None:
            first += f" The detector found {count} approximate moving interval(s)." + observed_windows
        else:
            first += " Timed motion phases could not be established from saved data."
        why = ("Gravity can accelerate an object downhill on an incline; friction and other effects "
               "can also influence its speed. However, tracking alone cannot prove which force "
               "caused each change, and short speed spikes may be noise.")
        physics = ("Average along-ramp velocity is signed displacement divided by elapsed time; "
                   "average path speed is the total tracked path divided by elapsed time. "
                   "Without length calibration and reliable end velocities, acceleration in m/s² "
                   "cannot be calculated responsibly.")
        takeaway = ("Repeat the run with a fixed camera, then compare a gentle and a steeper "
                    "ramp, changing only the incline. Compare recorded trends and note uncertainty.")
    return _as_text(dict(zip(HEADINGS, (first, why, physics, takeaway))))


INSTRUCTIONS = """You are the AI Motion Explanation in PhysiLearn, an evidence-led educational physics lab.
Write in natural, clear English for high-school students, explaining what moved, why the measured motion may have changed, and the science behind it.
Return exactly FOUR headings, each on its own line, followed by a short paragraph (45-80 words maximum per heading):
HOW IT MOVED
WHY IT CHANGED
PHYSICS BEHIND IT
WHAT WE LEARNED

HOW IT MOVED: narrate the actual recorded movement, citing specific time windows IF provided. If only interval count or averages exist, do not invent a chronological sequence. Never claim reversal based on the cumulative-distance plot: its values cannot reveal direction.
WHY IT CHANGED: explain plausible mechanisms with cautious phrasing ("could", "might"). Do NOT claim gravity/friction/pushing/acceleration caused changes unless the evidence supports it. If no reliable speed trend exists, explicitly say the cause is unknown; do not assert that speed rose or fell.
PHYSICS BEHIND IT: explain measured numbers, using average speed = distance/time; distinguish path vs displacement and speed vs velocity. Returning/backtracking can lower displacement but does not necessarily lower average speed. Link to verified formula values, do not invent any measurement.
WHAT WE LEARNED: one concrete conceptual takeaway and ONE doable next experiment linked to these findings, not a quiz.

Scientific constraints: use ONLY supplied saved measurements. Never claim pixels equal centimeters; ruler-calibrated values can be in cm. Avoid real SI acceleration/force without direct evidence. Speed peaks, direction changes and motion windows are estimates sensitive to tracking artifacts. A measured displacement larger than path is inconsistent: highlight uncertainty, never call it perfectly straight or round the ratio to 100%. Tracking gaps mean missing distance, not verified stops. For a ramp, distinguish signed downhill/uphill motion from speed. Avoid bulleted lists and markdown tables. No generic congratulations or invented precision.
"""


def explain_story_with_ai(lab, result):
    """Return (ai|offline, four-section text); no images or raw frame samples sent."""
    fallback = local_story_explanation(lab, result)
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")
    except ImportError:
        pass
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        print("Motion Story: no API key; showing local explanation.")
        return "offline", fallback
    try:
        from openai import OpenAI
        client = OpenAI(api_key=key, timeout=22.0, max_retries=0)
        response = client.responses.create(
            model=os.getenv("PHYSILEARN_AI_MODEL", "gpt-4o-mini"),
            instructions=INSTRUCTIONS,
            input=json.dumps(story_facts(lab, result), ensure_ascii=False),
            max_output_tokens=760,
            store=False,
        )
        content = (response.output_text or "").strip()
        parsed = parse_story_sections(content)
        if all(parsed.values()):
            return "ai", _as_text(parsed)
        print("Motion Story: incomplete explanation; showing local version.")
    except Exception as exc:
        # Never log raw exception contents, API key, or .env contents.
        print("Motion Story unavailable:", type(exc).__name__)
    return "offline", fallback
