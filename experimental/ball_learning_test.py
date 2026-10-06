import json
import os
import customtkinter as ctk


# ============================================================
# SETTINGS
# ============================================================

RESULT_FILE = "ball_experiment_result.json"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# ============================================================
# LOAD EXPERIMENT
# ============================================================

script_dir = os.path.dirname(
    os.path.abspath(__file__)
)

result_path = os.path.join(
    script_dir,
    RESULT_FILE
)

if not os.path.exists(result_path):
    raise FileNotFoundError(
        "ball_experiment_result.json was not found. "
        "Run ball_physics_test.py first."
    )

with open(
    result_path,
    "r",
    encoding="utf-8",
) as file:
    result = json.load(file)


distance = float(
    result["distance_traveled"]
)

displacement = float(
    result["horizontal_displacement"]
)

motion_time = float(
    result["motion_time"]
)

average_speed = float(
    result["average_speed"]
)

average_velocity = float(
    result["average_velocity"]
)

ball_size_variation = float(
    result["ball_size_variation_percent"]
)


# ============================================================
# APP
# ============================================================

app = ctk.CTk()

app.title(
    "PhysiLearn - Average Speed Challenge"
)

app.geometry(
    "900x700"
)

app.minsize(
    850,
    650
)


# ============================================================
# MAIN CONTAINER
# ============================================================

main_frame = ctk.CTkFrame(
    app,
    corner_radius=0,
)

main_frame.pack(
    fill="both",
    expand=True,
)


# ============================================================
# TITLE
# ============================================================

title = ctk.CTkLabel(
    main_frame,
    text="Your Ball Experiment",
    font=ctk.CTkFont(
        size=36,
        weight="bold",
    ),
)

title.pack(
    pady=(35, 5)
)


subtitle = ctk.CTkLabel(
    main_frame,
    text=(
        "PhysiLearn measured your real motion. "
        "Now use physics to analyze it."
    ),
    font=ctk.CTkFont(
        size=17
    ),
)

subtitle.pack(
    pady=(0, 20)
)


# ============================================================
# MEASUREMENTS CARD
# ============================================================

measurement_card = ctk.CTkFrame(
    main_frame,
    width=720,
    height=155,
    corner_radius=22,
)

measurement_card.pack(
    pady=5
)

measurement_card.pack_propagate(
    False
)


measurement_title = ctk.CTkLabel(
    measurement_card,
    text="MEASURED BY PHYSILEARN",
    font=ctk.CTkFont(
        size=16,
        weight="bold",
    ),
)

measurement_title.pack(
    pady=(18, 12)
)


values_frame = ctk.CTkFrame(
    measurement_card,
    fg_color="transparent",
)

values_frame.pack()


distance_box = ctk.CTkFrame(
    values_frame,
    width=200,
    height=75,
    corner_radius=15,
)

distance_box.pack(
    side="left",
    padx=10,
)

distance_box.pack_propagate(
    False
)


ctk.CTkLabel(
    distance_box,
    text="DISTANCE",
    font=ctk.CTkFont(
        size=13,
        weight="bold",
    ),
).pack(
    pady=(10, 2)
)


ctk.CTkLabel(
    distance_box,
    text=f"{distance:.3f} m",
    font=ctk.CTkFont(
        size=23,
        weight="bold",
    ),
).pack()


time_box = ctk.CTkFrame(
    values_frame,
    width=200,
    height=75,
    corner_radius=15,
)

time_box.pack(
    side="left",
    padx=10,
)

time_box.pack_propagate(
    False
)


ctk.CTkLabel(
    time_box,
    text="TIME",
    font=ctk.CTkFont(
        size=13,
        weight="bold",
    ),
).pack(
    pady=(10, 2)
)


ctk.CTkLabel(
    time_box,
    text=f"{motion_time:.3f} s",
    font=ctk.CTkFont(
        size=23,
        weight="bold",
    ),
).pack()


displacement_box = ctk.CTkFrame(
    values_frame,
    width=200,
    height=75,
    corner_radius=15,
)

displacement_box.pack(
    side="left",
    padx=10,
)

displacement_box.pack_propagate(
    False
)


ctk.CTkLabel(
    displacement_box,
    text="DISPLACEMENT",
    font=ctk.CTkFont(
        size=13,
        weight="bold",
    ),
).pack(
    pady=(10, 2)
)


ctk.CTkLabel(
    displacement_box,
    text=f"{displacement:+.3f} m",
    font=ctk.CTkFont(
        size=23,
        weight="bold",
    ),
).pack()


# ============================================================
# CHALLENGE CARD
# ============================================================

challenge_card = ctk.CTkFrame(
    main_frame,
    width=720,
    height=330,
    corner_radius=22,
)

challenge_card.pack(
    pady=18
)

challenge_card.pack_propagate(
    False
)


challenge_title = ctk.CTkLabel(
    challenge_card,
    text="CAN YOU CALCULATE THE AVERAGE SPEED?",
    font=ctk.CTkFont(
        size=19,
        weight="bold",
    ),
)

challenge_title.pack(
    pady=(25, 10)
)


question = ctk.CTkLabel(
    challenge_card,
    text=(
        "Use the distance and time measured "
        "from your own experiment."
    ),
    font=ctk.CTkFont(
        size=15
    ),
)

question.pack(
    pady=(0, 15)
)


formula = ctk.CTkLabel(
    challenge_card,
    text="v = d / t",
    font=ctk.CTkFont(
        size=30,
        weight="bold",
    ),
)

formula.pack(
    pady=(0, 15)
)


answer_frame = ctk.CTkFrame(
    challenge_card,
    fg_color="transparent",
)

answer_frame.pack()


answer_entry = ctk.CTkEntry(
    answer_frame,
    width=230,
    height=48,
    placeholder_text="Enter average speed",
    justify="center",
    font=ctk.CTkFont(
        size=17
    ),
)

answer_entry.pack(
    side="left",
    padx=(0, 10)
)


unit_label = ctk.CTkLabel(
    answer_frame,
    text="m/s",
    font=ctk.CTkFont(
        size=17,
        weight="bold",
    ),
)

unit_label.pack(
    side="left"
)


feedback_label = ctk.CTkLabel(
    challenge_card,
    text="",
    font=ctk.CTkFont(
        size=15
    ),
    wraplength=620,
    justify="center",
)

feedback_label.pack(
    pady=(15, 5)
)


solution_label = ctk.CTkLabel(
    challenge_card,
    text="",
    font=ctk.CTkFont(
        size=15
    ),
    wraplength=620,
    justify="center",
)

solution_label.pack(
    pady=(0, 5)
)


# ============================================================
# CHECK ANSWER
# ============================================================

def check_answer():

    raw_answer = (
        answer_entry.get()
        .strip()
        .replace(",", ".")
    )

    try:
        student_answer = float(
            raw_answer
        )

    except ValueError:

        feedback_label.configure(
            text=(
                "Enter a number, for example 0.14."
            )
        )

        solution_label.configure(
            text=""
        )

        return


    # Allow small rounding differences.

    tolerance = max(
        0.01,
        average_speed * 0.08
    )

    difference = abs(
        student_answer
        - average_speed
    )


    if difference <= tolerance:

        feedback_label.configure(
            text=(
                "Correct! You used measurements "
                "from your own experiment."
            )
        )

        solution_label.configure(
            text=(
                f"v = d / t\n"
                f"v = {distance:.3f} / "
                f"{motion_time:.3f}\n"
                f"v ≈ {average_speed:.3f} m/s"
            )
        )

    else:

        feedback_label.configure(
            text=(
                "Not quite. Remember: average speed "
                "uses total distance divided by time."
            )
        )

        solution_label.configure(
            text=(
                f"Try: {distance:.3f} ÷ "
                f"{motion_time:.3f}"
            )
        )


# ============================================================
# BUTTONS
# ============================================================

check_button = ctk.CTkButton(
    challenge_card,
    text="Check Answer",
    command=check_answer,
    width=210,
    height=45,
    corner_radius=14,
    font=ctk.CTkFont(
        size=16,
        weight="bold",
    ),
)

check_button.pack(
    pady=(10, 5)
)


# Press Enter to check.

answer_entry.bind(
    "<Return>",
    lambda event: check_answer()
)


# ============================================================
# ACCURACY NOTE
# ============================================================

accuracy_note = ctk.CTkLabel(
    main_frame,
    text=(
        "Estimated camera-based measurements  •  "
        f"Ball-size variation: "
        f"{ball_size_variation:.1f}%"
    ),
    font=ctk.CTkFont(
        size=12
    ),
)

accuracy_note.pack(
    pady=(0, 10)
)


# ============================================================
# START
# ============================================================

answer_entry.focus()

app.mainloop()