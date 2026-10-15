"""One evidence-aware physics principle for a recorded PhysiLearn experiment.

No API call. No numeric force/acceleration estimate from noisy webcam data.
"""
from __future__ import annotations


def choose_physics_principle(lab: str, result: dict, motion_report: dict) -> dict:
    """Return a concept, a textbook law, and an honest note on its limits.

    The card teaches the physics principle; it does not assert a measured force.
    """
    if lab == "ramp":
        return {
            "title": "GRAVITY ON AN INCLINED PLANE",
            "formula": "F_parallel = m × g × sin(θ)",
            "explanation": (
                "Gravity has a component parallel to the ramp, directed downhill. "
                "This helps explain why an object can change its motion on an incline. "
                "The actual motion also depends on friction, contact forces, and (for a rolling object) rotation."
            ),
            "limitation": (
                "This is the downhill component of gravity, NOT the measured net force. "
                "Mass and ramp angle were not measured here, so the force is not calculated."
            ),
        }

    segments = motion_report.get("segments", []) if isinstance(motion_report, dict) else []
    has_estimated_speed_change = any(
        "estimated speed rose" in str(s.get("description", "")).lower()
        and "decreased" in str(s.get("description", "")).lower()
        for s in segments if isinstance(s, dict)
    )
    if has_estimated_speed_change:
        return {
            "title": "NEWTON'S SECOND LAW",
            "formula": "ΣF = m × a",
            "explanation": (
                "The tracking estimates suggest that speed increased and later decreased during part of this run. "
                "Newton's second law connects a change in velocity (acceleration) with a net force. "
                "A push or friction may play a role, but the recording cannot identify the cause."
            ),
            "limitation": (
                "The speed trend is approximate and may include tracking noise. "
                "Neither mass nor reliable acceleration was measured, so no force value can be calculated."
            ),
        }

    return {
        "title": "NEWTON'S FIRST LAW · INERTIA",
        "formula": "ΣF = 0  →  velocity stays constant",
        "explanation": (
            "Newton's first law says that an object's velocity remains unchanged "
            "if the net external force is zero. An object does not need a continuous push "
            "to maintain its velocity. This is a useful principle for thinking about starts, stops and motion."
        ),
        "limitation": (
            "This recording does not establish that the net force was zero or that the car moved "
            "at constant velocity. Use the measured speed trend to evaluate such claims."
        ),
    }
