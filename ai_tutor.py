import os

from dotenv import load_dotenv
from openai import OpenAI


# ============================================================
# PHYSILEARN THRESHOLDS
# ============================================================

DIRECTION_THRESHOLD = 85.0
VELOCITY_VARIATION_THRESHOLD = 0.25
ACCELERATION_THRESHOLD = 0.45


# ============================================================
# FEATHERLESS AI SETUP
# ============================================================

load_dotenv()

api_key = os.getenv("FEATHERLESS_API_KEY")

client = None

if api_key:
    client = OpenAI(
        base_url="https://api.featherless.ai/v1",
        api_key=api_key,
    )


# ============================================================
# HELPERS
# ============================================================

def safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def metric_results(
    direction,
    variation,
    acceleration,
):
    return {
        "direction": (
            direction >= DIRECTION_THRESHOLD
        ),
        "variation": (
            variation < VELOCITY_VARIATION_THRESHOLD
        ),
        "acceleration": (
            acceleration < ACCELERATION_THRESHOLD
        ),
    }


def get_failed_metrics(
    direction,
    variation,
    acceleration,
):
    results = metric_results(
        direction,
        variation,
        acceleration,
    )

    failed = []

    if not results["direction"]:
        deficit = (
            DIRECTION_THRESHOLD - direction
        ) / DIRECTION_THRESHOLD

        failed.append(
            (
                deficit,
                "direction",
            )
        )

    if not results["variation"]:
        deficit = (
            variation
            - VELOCITY_VARIATION_THRESHOLD
        ) / VELOCITY_VARIATION_THRESHOLD

        failed.append(
            (
                deficit,
                "variation",
            )
        )

    if not results["acceleration"]:
        deficit = (
            acceleration
            - ACCELERATION_THRESHOLD
        ) / ACCELERATION_THRESHOLD

        failed.append(
            (
                deficit,
                "acceleration",
            )
        )

    failed.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    return failed


def get_weakest_pass_metric(
    direction,
    variation,
    acceleration,
):
    """
    Finds the PASS measurement closest to its threshold.
    That becomes the optional improvement challenge.
    """

    direction_margin = (
        direction - DIRECTION_THRESHOLD
    ) / (
        100.0 - DIRECTION_THRESHOLD
    )

    variation_margin = (
        VELOCITY_VARIATION_THRESHOLD
        - variation
    ) / VELOCITY_VARIATION_THRESHOLD

    acceleration_margin = (
        ACCELERATION_THRESHOLD
        - acceleration
    ) / ACCELERATION_THRESHOLD

    margins = {
        "direction": direction_margin,
        "variation": variation_margin,
        "acceleration": acceleration_margin,
    }

    return min(
        margins,
        key=margins.get,
    )


# ============================================================
# DETERMINISTIC WHAT HAPPENED
# ============================================================

def build_measurement_summary(
    status,
    direction,
    variation,
    acceleration,
):
    results = metric_results(
        direction,
        variation,
        acceleration,
    )

    direction_word = (
        "passed"
        if results["direction"]
        else "missed"
    )

    variation_word = (
        "passed"
        if results["variation"]
        else "missed"
    )

    acceleration_word = (
        "passed"
        if results["acceleration"]
        else "missed"
    )

    if status == "PASS":
        return (
            f"You passed the constant-velocity challenge. "
            f"Direction consistency was {direction:.1f}% "
            f"(target ≥ {DIRECTION_THRESHOLD:.0f}%), "
            f"velocity variation was {variation:.3f} "
            f"(target < {VELOCITY_VARIATION_THRESHOLD:.2f}), "
            f"and average acceleration was {acceleration:.3f} "
            f"(target < {ACCELERATION_THRESHOLD:.2f}). "
            f"All three measurements met the experiment targets."
        )

    failed = get_failed_metrics(
        direction,
        variation,
        acceleration,
    )

    failed_names = [
        item[1]
        for item in failed
    ]

    if failed_names:
        readable = []

        if "direction" in failed_names:
            readable.append(
                "direction consistency"
            )

        if "variation" in failed_names:
            readable.append(
                "velocity variation"
            )

        if "acceleration" in failed_names:
            readable.append(
                "average acceleration"
            )

        if len(readable) == 1:
            failure_text = readable[0]

        elif len(readable) == 2:
            failure_text = (
                f"{readable[0]} and "
                f"{readable[1]}"
            )

        else:
            failure_text = (
                f"{readable[0]}, "
                f"{readable[1]}, and "
                f"{readable[2]}"
            )

    else:
        failure_text = "the experiment criteria"

    return (
        f"Your direction consistency was {direction:.1f}% "
        f"({direction_word} the target), "
        f"velocity variation was {variation:.3f} "
        f"({variation_word} the target), and "
        f"average acceleration was {acceleration:.3f} "
        f"({acceleration_word} the target). "
        f"The TRY AGAIN result was caused by "
        f"{failure_text}."
    )


# ============================================================
# DETERMINISTIC PHYSICS
# ============================================================

def build_physics_explanation(
    direction,
    variation,
    acceleration,
):
    return (
        "Velocity describes how position changes over time:\n"
        "v = Δx / Δt\n\n"
        "Acceleration describes how velocity changes over time:\n"
        "a = Δv / Δt\n\n"
        "Velocity includes both speed and direction. "
        "For constant velocity, the object should keep moving "
        "in the same direction at approximately the same speed. "
        "That keeps Δv small, so acceleration should also stay low."
    )


# ============================================================
# DETERMINISTIC TRY NEXT
# ============================================================

def build_try_next(
    status,
    direction,
    variation,
    acceleration,
):
    if status == "PASS":

        weakest = get_weakest_pass_metric(
            direction,
            variation,
            acceleration,
        )

        if weakest == "direction":
            return (
                f"Your direction consistency was "
                f"{direction:.1f}%. As an extra challenge, "
                "move in one straight left-to-right path "
                "and see if you can bring it even closer "
                "to 100%."
            )

        if weakest == "variation":
            return (
                f"Your velocity variation was "
                f"{variation:.3f}. As an extra challenge, "
                "make the motion even smoother and see if "
                "you can reduce that value."
            )

        return (
            f"Your average acceleration was "
            f"{acceleration:.3f}. As an extra challenge, "
            "change your speed even less during the motion "
            "and see if you can lower that value."
        )

    failed = get_failed_metrics(
        direction,
        variation,
        acceleration,
    )

    if not failed:
        return (
            "Try the experiment again while moving smoothly "
            "from left to right at a steady speed."
        )

    biggest_problem = failed[0][1]

    if biggest_problem == "direction":
        return (
            f"Direction consistency was only "
            f"{direction:.1f}% while the target is at least "
            f"{DIRECTION_THRESHOLD:.0f}%. "
            "Move continuously from left to right without "
            "reversing direction."
        )

    if biggest_problem == "variation":
        return (
            f"Velocity variation was {variation:.3f} "
            f"while the target is below "
            f"{VELOCITY_VARIATION_THRESHOLD:.2f}. "
            "Try moving at a steadier speed instead of "
            "speeding up and slowing down."
        )

    return (
        f"Average acceleration was {acceleration:.3f} "
        f"while the target is below "
        f"{ACCELERATION_THRESHOLD:.2f}. "
        "Make the motion smoother so that your velocity "
        "changes less during the experiment."
    )


# ============================================================
# OPTIONAL AI COACH SENTENCE
# ============================================================

def generate_ai_coach_note(
    status,
    direction,
    variation,
    acceleration,
):
    """
    AI does NOT grade the experiment.
    It only produces one short personalized coaching sentence.
    """

    if client is None:
        return ""

    failed = get_failed_metrics(
        direction,
        variation,
        acceleration,
    )

    if failed:
        main_issue = failed[0][1]
    else:
        main_issue = "none"

    prompt = f"""
A student completed a PhysiLearn physics experiment.

Official result: {status}

Measurements:
Direction consistency: {direction:.1f}%
Velocity variation: {variation:.3f}
Average acceleration: {acceleration:.3f}

Thresholds:
Direction consistency >= 85%
Velocity variation < 0.25
Average acceleration < 0.45

Most important failed metric:
{main_issue}

Write ONE short encouraging sentence explaining the student's
result in simple English.

Rules:
- Do not change the official result.
- Do not invent measurements.
- Do not invent units.
- If only one metric failed, do not claim that other metrics failed.
- Maximum 35 words.
- No heading.
- No bullet point.
"""

    try:
        response = client.chat.completions.create(
            model="Qwen/Qwen2.5-7B-Instruct",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a short educational coaching assistant. "
                        "The rule-based evaluator is authoritative. "
                        "Never override its measurements or result."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.2,
            max_tokens=80,
        )

        note = response.choices[0].message.content

        if not note:
            return ""

        return note.strip()

    except Exception as error:
        print(
            f"AI Coach note unavailable: {error}"
        )

        return ""


# ============================================================
# MAIN TUTOR FUNCTION
# ============================================================

def generate_tutor_feedback(
    status,
    direction_consistency,
    velocity_variation,
    average_acceleration,
    concept,
):
    """
    Returns a stable, structured explanation.

    Physics, grading, thresholds, and improvement advice
    are produced deterministically by Python.

    Featherless AI only provides an optional short coaching
    sentence.
    """

    direction = safe_float(
        direction_consistency
    )

    variation = safe_float(
        velocity_variation
    )

    acceleration = safe_float(
        average_acceleration
    )

    # --------------------------------------------------------
    # NOT ENOUGH DATA
    # --------------------------------------------------------

    if (
        direction is None
        or variation is None
        or acceleration is None
    ):
        return (
            "WHAT HAPPENED\n"
            "PhysiLearn could not collect enough reliable motion "
            "data to evaluate this attempt.\n\n"

            "PHYSICS\n"
            "Velocity describes how position changes over time:\n"
            "v = Δx / Δt\n\n"
            "Acceleration describes how velocity changes over time:\n"
            "a = Δv / Δt\n\n"
            "Reliable measurements require the tracked object to "
            "remain visible throughout the experiment.\n\n"

            "TRY NEXT\n"
            "Keep the tracked object clearly visible in the webcam "
            "for the entire recording."
        )

    # Normalize status

    normalized_status = (
        "PASS"
        if str(status).upper() == "PASS"
        else "TRY_AGAIN"
    )

    what_happened = build_measurement_summary(
        normalized_status,
        direction,
        variation,
        acceleration,
    )

    physics = build_physics_explanation(
        direction,
        variation,
        acceleration,
    )

    try_next = build_try_next(
        normalized_status,
        direction,
        variation,
        acceleration,
    )

    ai_note = generate_ai_coach_note(
        normalized_status,
        direction,
        variation,
        acceleration,
    )

    if ai_note:
        what_happened = (
            f"{what_happened}\n\n"
            f"AI Tutor: {ai_note}"
        )

    return (
        "WHAT HAPPENED\n"
        f"{what_happened}\n\n"

        "PHYSICS\n"
        f"{physics}\n\n"

        "TRY NEXT\n"
        f"{try_next}"
    )


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":

    print(
        "Testing PhysiLearn AI Physics Tutor...\n"
    )

    # Yesterday's real TRY AGAIN result:
    test_feedback = generate_tutor_feedback(
        status="TRY_AGAIN",
        direction_consistency=67.5,
        velocity_variation=0.246,
        average_acceleration=0.320,
        concept=(
            "Constant velocity requires both constant "
            "speed and constant direction."
        ),
    )

    print(
        "PHYSILEARN AI PHYSICS TUTOR\n"
    )

    print(test_feedback)