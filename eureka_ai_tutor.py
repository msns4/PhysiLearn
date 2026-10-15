"""AI Physics Tutor for Eureka labs; no API key is needed for the local explanation.

An OpenAI-powered response is used only when OPENAI_API_KEY is configured.
Data in AI requests is limited to numerical summaries and generic object labels.
"""
import os


def _fmt(value, decimals=2):
    try:
        return f"{float(value):.{decimals}f}"
    except (TypeError, ValueError):
        return "N/A"


def facts_for_tutor(lab, result):
    if lab == "object":
        unit = result.get("measurement_units", "px")
        facts = {
            "lab": "Object Physics Lab",
            "object": result.get("object_name", "Object"),
            "distance": result.get("distance"),
            "displacement_magnitude": result.get("displacement_magnitude"),
            "duration_s": result.get("duration_s"),
            "average_speed": result.get("average_speed"),
            "unit": unit,
            "calibrated": bool(result.get("calibration_used", False)),
        }
    else:
        facts = {
            "lab": "Ramp Physics Lab",
            "recording_time_s": result.get("duration_s"),
            "estimated_moving_time_s": result.get("approx_motion_duration_s"),
            "position_change_along_ramp_px": result.get("along_ramp_displacement_px"),
            "estimated_path_along_ramp_px": result.get("approx_along_ramp_path_px"),
            "estimated_peak_downhill_velocity_px_per_s": result.get("peak_downhill_velocity_px_s"),
            "unit": "pixel", "calibrated": False,
        }
    # Physics Tutor 2.0: computed facts, never raw frames or the API key.
    from eureka_motion_analysis import build_motion_report, build_formula_cards
    motion = build_motion_report(lab, result)
    formulas = build_formula_cards(lab, result)
    facts["deterministic_motion_analysis"] = motion["ai_facts"]
    facts["verified_formulas"] = [card["ai_fact"] for card in formulas]
    facts["science_note"] = (
        "Motion intervals are approximate and camera noise may affect peaks. "
        "Do not state exact acceleration without reliable measurements. "
        "Pixel units are not physical SI units."
    )
    return facts


def local_explanation(lab, result):
    if lab == "object":
        unit = result.get("measurement_units", "px")
        name = result.get("object_name", "Object")
        path = result.get("distance")
        displacement = result.get("displacement_magnitude")
        duration = result.get("duration_s")
        speed = result.get("average_speed")
        relative = ""
        try:
            if float(path) > 0:
                ratio = float(displacement) / float(path)
                if ratio >= .85:
                    relative = "The path and displacement are close, suggesting mostly one-way motion. "
                elif ratio <= .20:
                    relative = "The displacement is much smaller than the path, suggesting a return or change in direction. "
                else:
                    relative = "The path is longer than the final separation, consistent with some changes of direction. "
        except (ValueError, TypeError, ZeroDivisionError):
            pass
        limits = ("This is an image-space estimate; pixel speed is not a real-world speed."
                  if unit == "px" else
                  "Calibrated values are approximate and depend on accurate ruler placement.")
        return (f"WHAT HAPPENED\n{name} traveled about {_fmt(path)} {unit} over "
                f"{_fmt(duration)} seconds. Its start-to-end separation was {_fmt(displacement)} {unit}. "
                f"{relative}\n\nPHYSICS\nAverage speed = total path / recording time = "
                f"{_fmt(speed)} {unit}/s. It includes time when the object was stationary. "
                f"{limits} Tracking noise can affect the estimates.\n\nTRY NEXT\n"
                "Try moving the same object forward and back. Compare total path with "
                "start-to-end displacement, or calibrate using a real ruler.")

    move_t = result.get("approx_motion_duration_s")
    extra = (f"Motion was detected for approximately {_fmt(move_t)} s. " if move_t is not None else "")
    return (
        "WHAT HAPPENED\nThe car moved along the ramp by approximately "
        f"{_fmt(result.get('along_ramp_displacement_px'))} image pixels. "
        f"{extra}The largest estimated downhill velocity was "
        f"{_fmt(result.get('peak_downhill_velocity_px_s'))} px/s.\n\n"
        "PHYSICS\nAs a car rolls downhill, gravity can cause its velocity to increase. "
        "The graph should be read in stages: stationary, motion, then stopping. "
        "The sharp speed drop near the bottom may include braking or tracker noise. "
        "These pixel measurements do not by themselves give true acceleration in m/s².\n\n"
        "TRY NEXT\nRepeat the run with the same setup, then compare a gentle incline "
        "with a slightly steeper incline. Keep the camera fixed and avoid pushing the car."
    )


def explain_with_ai(lab, result):
    """Return (source, explanation). Send summary facts only; no camera images."""
    fallback = local_explanation(lab, result)
    try:
        from dotenv import load_dotenv
        from pathlib import Path
        load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")
    except ImportError:
        pass

    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        print("AI Tutor: OPENAI_API_KEY not set; using local physics explanation.")
        return ("offline", fallback)

    try:
        from openai import OpenAI
        import json
        client = OpenAI(api_key=key, timeout=20.0, max_retries=0)
        prompt = json.dumps(facts_for_tutor(lab, result), ensure_ascii=False)
        response = client.responses.create(
            model=os.getenv("PHYSILEARN_AI_MODEL", "gpt-4o-mini"),
            instructions=(
                "You are a careful high-school physics tutor. Write concise English under "
                "exact headings WHAT HAPPENED, PHYSICS, TRY NEXT (one paragraph each). "
                "Use ONLY the given data, never invent metrics, causes, forces or actual-world "
                "cm/m/s values from pixel data. Distinguish average speed over full recording "
                "from instantaneous/peak velocity. Tracking and projection can have errors. "
                "Discuss detected motion intervals when available and explain the verified "
                "formula results; distinguish motion estimates from facts. "
                "Keep each section concise (under 90 words), avoid markdown bullet lists, "
                "be encouraging and suggest one simple follow-up test."
            ),
            input=prompt,
            max_output_tokens=500,
            store=False,
        )
        content = (response.output_text or "").strip()
        if all(h in content.upper() for h in ("WHAT HAPPENED", "PHYSICS", "TRY NEXT")):
            return ("ai", content)
        print("AI Tutor: response missing expected headings; using local explanation.")
    except Exception as exc:
        # Never print API tokens, .env contents, or raw exception messages.
        print("AI Tutor temporarily unavailable:", type(exc).__name__)
    return ("offline", fallback)
