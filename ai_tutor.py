import os

from dotenv import load_dotenv
from openai import OpenAI


# =========================================================
# LOAD API KEY
# =========================================================

load_dotenv()

api_key = os.getenv("FEATHERLESS_API_KEY")

if not api_key:
    raise ValueError(
        "FEATHERLESS_API_KEY was not found in .env"
    )


# =========================================================
# FEATHERLESS CLIENT
# =========================================================

client = OpenAI(
    base_url="https://api.featherless.ai/v1",
    api_key=api_key
)


# =========================================================
# AI PHYSICS TUTOR
# =========================================================

def generate_tutor_feedback(
    status,
    direction_consistency,
    velocity_variation,
    average_acceleration,
    concept
):

    prompt = f"""
A student just completed a physics experiment in PhysiLearn.

Challenge:
Move a hand from left to right at approximately constant velocity.

The computer vision system measured:

Result: {status}
Direction consistency: {direction_consistency}%
Velocity variation: {velocity_variation}
Average acceleration: {average_acceleration}

Physics concept:
{concept}

Explain the result to the student.

Requirements:
- Use simple, encouraging English.
- Be concise: about 3 to 5 sentences.
- Explain WHY the student passed or needs to try again.
- Use the measurements provided.
- Do not change or question the PASS/TRY_AGAIN result.
- Do not invent measurements.
- Explain the relevant physics concept.
- If improvement is needed, give one practical suggestion.
"""

    response = client.chat.completions.create(
        model="Qwen/Qwen2.5-7B-Instruct",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are the AI Physics Tutor inside "
                    "PhysiLearn, an interactive educational "
                    "physics application. Explain experimental "
                    "results clearly and accurately to students."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.4,
        max_tokens=220
    )

    return response.choices[0].message.content


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    print("\nConnecting to Featherless AI...\n")

    feedback = generate_tutor_feedback(
        status="PASS",
        direction_consistency=100.0,
        velocity_variation=0.124,
        average_acceleration=0.201,
        concept=(
            "Constant velocity requires both "
            "constant speed and constant direction."
        )
    )

    print("----------------------------------")
    print("PHYSILEARN AI PHYSICS TUTOR")
    print("----------------------------------")
    print(feedback)
    print("----------------------------------")