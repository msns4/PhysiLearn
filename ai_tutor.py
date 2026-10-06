import os

from dotenv import load_dotenv
from openai import OpenAI


# ============================================================
# PHYSILEARN SETTINGS
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
# GENERAL HELPERS
# ============================================================

def safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ============================================================
# HAND EXPERIMENT HELPERS
# ============================================================

def metric_results(
    direction,
    variation,
    acceleration,
):
    return {
        "direction": direction >= DIRECTION_THRESHOLD,
        "variation": variation < VELOCITY_VARIATION_THRESHOLD,
        "acceleration": acceleration < ACCELERATION_THRESHOLD,
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
# HAND — WHAT HAPPENED
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
            f"{readable[0]} and {readable[1]}"
        )

    elif len(readable) >= 3:
        failure_text = (
            f"{readable[0]}, "
            f"{readable[1]}, and "
            f"{readable[2]}"
        )

    else:
        failure_text = (
            "the experiment criteria"
        )

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
# HAND — PHYSICS
# ============================================================

def build_physics_explanation():
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
# HAND — TRY NEXT
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
# HAND — FEATHERLESS COACH
# ============================================================

def generate_hand_ai_note(
    status,
    direction,
    variation,
    acceleration,
):
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
A student completed a PhysiLearn hand-motion physics experiment.

Official result: {status}

Verified measurements:
Direction consistency: {direction:.1f}%
Velocity variation: {variation:.3f}
Average acceleration: {acceleration:.3f}

Thresholds:
Direction consistency >= 85%
Velocity variation < 0.25
Average acceleration < 0.45

Most important failed metric:
{main_issue}

Write ONE short encouraging coaching sentence.

Rules:
- The evaluator result is final.
- Do not change the result.
- Do not invent measurements.
- Do not invent units.
- If only one metric failed, do not claim others failed.
- Maximum 35 words.
- No heading.
"""

    try:
        response = client.chat.completions.create(
            model="Qwen/Qwen2.5-7B-Instruct",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are the AI Physics Tutor inside PhysiLearn. "
                        "Deterministic physics code decides the result. "
                        "Your role is only to provide a short, helpful "
                        "coaching sentence."
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
            f"Hand AI Tutor unavailable: {error}"
        )

        return ""


# ============================================================
# HAND — MAIN TUTOR FUNCTION
# ============================================================

def generate_tutor_feedback(
    status,
    direction_consistency,
    velocity_variation,
    average_acceleration,
    concept,
):
    direction = safe_float(
        direction_consistency
    )

    variation = safe_float(
        velocity_variation
    )

    acceleration = safe_float(
        average_acceleration
    )

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

            "TRY NEXT\n"
            "Keep your hand clearly visible to the webcam "
            "for the entire recording."
        )

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

    physics = build_physics_explanation()

    try_next = build_try_next(
        normalized_status,
        direction,
        variation,
        acceleration,
    )

    ai_note = generate_hand_ai_note(
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
# BALL LAB — DETERMINISTIC PHYSICS
# ============================================================

def build_ball_physics_feedback(
    distance,
    motion_time,
    displacement,
    average_speed,
    average_velocity,
    ball_size_variation,
):
    displacement_magnitude = abs(
        displacement
    )

    difference = abs(
        distance - displacement_magnitude
    )

    if distance > 0:
        difference_percent = (
            difference
            / distance
            * 100.0
        )
    else:
        difference_percent = 0.0

    if difference_percent < 10:
        relationship_text = (
            "The total distance and the magnitude of the horizontal "
            "displacement were close. This means the tracked distance "
            "was similar to the change between the starting and ending "
            "horizontal positions."
        )

    else:
        relationship_text = (
            "The total distance was larger than the magnitude of the "
            "horizontal displacement. Distance adds up the tracked "
            "motion, while horizontal displacement compares only the "
            "starting and ending horizontal positions."
        )

    if displacement > 0:
        direction_text = (
            "The positive horizontal velocity means the ending "
            "horizontal position was to the right of the starting "
            "position."
        )

    elif displacement < 0:
        direction_text = (
            "The negative horizontal velocity means the ending "
            "horizontal position was to the left of the starting "
            "position."
        )

    else:
        direction_text = (
            "The horizontal displacement was close to zero, meaning "
            "the starting and ending horizontal positions were nearly "
            "the same."
        )

    if ball_size_variation <= 10:
        calibration_text = (
            f"Ball-size variation was {ball_size_variation:.1f}%, "
            "so the webcam scale stayed fairly stable during this "
            "attempt."
        )

    elif ball_size_variation <= 15:
        calibration_text = (
            f"Ball-size variation was {ball_size_variation:.1f}%. "
            "The measurement is still useful as an estimate, but "
            "keeping the ball at a more constant distance from the "
            "camera could improve consistency."
        )

    else:
        calibration_text = (
            f"Ball-size variation was {ball_size_variation:.1f}%. "
            "For a better estimate, keep the ball at a more constant "
            "distance from the camera during the next attempt."
        )

    what_happened = (
        f"Your ball traveled approximately {distance:.3f} m "
        f"in {motion_time:.3f} s. "
        f"The measured average speed was {average_speed:.3f} m/s, "
        f"and the horizontal average velocity was "
        f"{average_velocity:+.3f} m/s."
    )

    physics = (
        "Average speed uses total distance traveled:\n"
        "v = d / t\n\n"
        f"v = {distance:.3f} / {motion_time:.3f} "
        f"= {average_speed:.3f} m/s\n\n"

        "Horizontal average velocity uses horizontal displacement:\n"
        "v_horizontal = displacement / time\n\n"
        f"v_horizontal = {displacement:+.3f} / "
        f"{motion_time:.3f} "
        f"= {average_velocity:+.3f} m/s\n\n"

        f"{relationship_text} "
        f"{direction_text}"
    )

    try_next = (
        f"{calibration_text} "
        "For the next experiment, try rolling the ball away and then "
        "back toward its starting position. Compare how total distance "
        "and horizontal displacement change."
    )

    return (
        what_happened,
        physics,
        try_next,
    )


# ============================================================
# BALL LAB — FEATHERLESS COACH
# ============================================================

def generate_ball_ai_note(
    distance,
    motion_time,
    displacement,
    average_speed,
    average_velocity,
    ball_size_variation,
):
    if client is None:
        return ""

    displacement_magnitude = abs(
        displacement
    )

    if distance > 0:
        difference_percent = (
            abs(
                distance
                - displacement_magnitude
            )
            / distance
            * 100.0
        )
    else:
        difference_percent = 0.0

    if difference_percent < 10:
        relationship = (
            "distance and horizontal displacement magnitude "
            "were close"
        )
    else:
        relationship = (
            "distance was noticeably larger than horizontal "
            "displacement magnitude"
        )

    if ball_size_variation <= 10:
        calibration_quality = "stable"
    elif ball_size_variation <= 15:
        calibration_quality = "moderately stable"
    else:
        calibration_quality = "less stable"

    prompt = f"""
A student completed a tennis-ball experiment in PhysiLearn.

The deterministic physics system has already verified the results.

Verified facts:
- Distance: {distance:.3f} m
- Time: {motion_time:.3f} s
- Horizontal displacement: {displacement:+.3f} m
- Average speed: {average_speed:.3f} m/s
- Horizontal average velocity: {average_velocity:+.3f} m/s
- Distance/displacement relationship:
  {relationship}
- Webcam calibration quality:
  {calibration_quality}

Write ONE short personalized coaching sentence for the student.

Rules:
- Maximum 35 words.
- Do not calculate anything.
- Do not invent motion details.
- Do not mention diagonal, curved, upward, or downward motion.
- Do not claim anything not listed in the verified facts.
- Do not use LaTeX.
- Do not change any measurements.
- Focus on what the student could explore next.
- No heading.
"""

    try:
        response = client.chat.completions.create(
            model="Qwen/Qwen2.5-7B-Instruct",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are the AI Physics Coach inside PhysiLearn. "
                        "All measurements and physics conclusions come "
                        "from deterministic code. You only provide one "
                        "short coaching suggestion based on verified facts."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.15,
            max_tokens=80,
        )

        note = response.choices[0].message.content

        if not note:
            return ""

        return note.strip()

    except Exception as error:
        print(
            f"Ball AI Tutor unavailable: {error}"
        )

        return ""


# ============================================================
# BALL LAB — MAIN TUTOR FUNCTION
# ============================================================

def generate_ball_tutor_feedback(
    distance,
    motion_time,
    displacement,
    average_speed,
    average_velocity,
    ball_size_variation,
):
    distance = safe_float(
        distance
    )

    motion_time = safe_float(
        motion_time
    )

    displacement = safe_float(
        displacement
    )

    average_speed = safe_float(
        average_speed
    )

    average_velocity = safe_float(
        average_velocity
    )

    ball_size_variation = safe_float(
        ball_size_variation
    )

    values = [
        distance,
        motion_time,
        displacement,
        average_speed,
        average_velocity,
        ball_size_variation,
    ]

    if any(
        value is None
        for value in values
    ):
        return (
            "WHAT HAPPENED\n"
            "PhysiLearn could not load all of the ball experiment "
            "measurements.\n\n"

            "PHYSICS CONNECTION\n"
            "Average speed is calculated using v = d / t.\n\n"

            "TRY NEXT\n"
            "Run the ball experiment again while keeping the tennis "
            "ball clearly visible to the webcam."
        )

    (
        what_happened,
        physics,
        try_next,
    ) = build_ball_physics_feedback(
        distance,
        motion_time,
        displacement,
        average_speed,
        average_velocity,
        ball_size_variation,
    )

    ai_note = generate_ball_ai_note(
        distance,
        motion_time,
        displacement,
        average_speed,
        average_velocity,
        ball_size_variation,
    )

    if ai_note:
        try_next = (
            f"{try_next}\n\n"
            f"AI Tutor: {ai_note}"
        )

    return (
        "WHAT HAPPENED\n"
        f"{what_happened}\n\n"

        "PHYSICS CONNECTION\n"
        f"{physics}\n\n"

        "TRY NEXT\n"
        f"{try_next}"
    )


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":

    print()
    print(
        "=========================================="
    )
    print(
        "TEST 1 — HAND MOTION AI TUTOR"
    )
    print(
        "=========================================="
    )
    print()

    hand_feedback = generate_tutor_feedback(
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
        hand_feedback
    )

    print()
    print()
    print(
        "=========================================="
    )
    print(
        "TEST 2 — BALL PHYSICS AI TUTOR"
    )
    print(
        "=========================================="
    )
    print()

    ball_feedback = generate_ball_tutor_feedback(
        distance=0.376,
        motion_time=2.911,
        displacement=0.352,
        average_speed=0.129,
        average_velocity=0.121,
        ball_size_variation=7.2,
    )

    print(
        ball_feedback
    )