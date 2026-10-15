import customtkinter as ctk

import subprocess

import sys

import os

import json

import threading



from ai_tutor import (
    generate_tutor_feedback,
    generate_ball_tutor_feedback,
)





# =========================================================

# APP SETUP

# =========================================================



ctk.set_appearance_mode("dark")

ctk.set_default_color_theme("blue")



app = ctk.CTk()



app.title("PhysiLearn")

app.geometry("1100x760")

app.minsize(1000, 700)





# =========================================================

# HELPERS

# =========================================================



def clear_screen():



    for widget in app.winfo_children():

        widget.destroy()





def project_file(filename):



    project_dir = os.path.dirname(

        os.path.abspath(__file__)

    )



    return os.path.join(

        project_dir,

        filename

    )






def format_measurement(value, decimals=3, suffix=""):
    """Format a numeric measurement for the result screen."""

    if value == "N/A" or value is None:
        return "N/A"

    try:
        return f"{float(value):.{decimals}f}{suffix}"

    except (TypeError, ValueError):
        return f"{value}{suffix}"


def parse_ai_sections(ai_feedback):
    """
    Split the AI Tutor response into stable UI sections.

    The AI Tutor is asked to return these headings, but the UI still
    has safe defaults in case an unexpected response reaches the app.
    """

    sections = {
        "WHAT HAPPENED": "",
        "PHYSICS": "",
        "TRY NEXT": "",
    }

    if not isinstance(ai_feedback, str):
        ai_feedback = ""

    current_section = None

    for raw_line in ai_feedback.replace("\r\n", "\n").split("\n"):

        line = raw_line.strip()

        if line.upper() in sections:
            current_section = line.upper()
            continue

        if current_section and line:
            if sections[current_section]:
                sections[current_section] += "\n"

            sections[current_section] += line

    if not sections["WHAT HAPPENED"]:
        cleaned = ai_feedback.strip()

        sections["WHAT HAPPENED"] = (
            cleaned
            if cleaned
            else "PhysiLearn analyzed your motion successfully."
        )

    if not sections["PHYSICS"]:
        sections["PHYSICS"] = (
            "Velocity describes how position changes over time:\n"
            "v = Δx / Δt\n\n"
            "Acceleration describes how velocity changes over time:\n"
            "a = Δv / Δt\n\n"
            "Constant velocity requires both steady speed and "
            "steady direction."
        )

    if not sections["TRY NEXT"]:
        sections["TRY NEXT"] = (
            "Repeat the experiment and try to make your motion "
            "even smoother."
        )

    return sections


def parse_ball_ai_sections(ai_feedback):
    """Split Ball Lab AI feedback into stable UI sections."""

    sections = {
        "WHAT HAPPENED": "",
        "PHYSICS CONNECTION": "",
        "TRY NEXT": "",
    }

    if not isinstance(ai_feedback, str):
        ai_feedback = ""

    current_section = None

    for raw_line in ai_feedback.replace("\r\n", "\n").split("\n"):
        line = raw_line.strip()
        heading = line.upper()

        if heading in sections:
            current_section = heading
            continue

        if current_section and line:
            if sections[current_section]:
                sections[current_section] += "\n"
            sections[current_section] += line

    if not sections["WHAT HAPPENED"]:
        sections["WHAT HAPPENED"] = (
            ai_feedback.strip()
            or "PhysiLearn analyzed your ball experiment successfully."
        )

    if not sections["PHYSICS CONNECTION"]:
        sections["PHYSICS CONNECTION"] = (
            "Average speed uses total distance divided by time: "
            "v = d / t. Velocity uses displacement, so direction matters."
        )

    if not sections["TRY NEXT"]:
        sections["TRY NEXT"] = (
            "Try another roll and compare how changing the path changes "
            "distance, displacement, and average velocity."
        )

    return sections


# =========================================================

# HOME SCREEN

# =========================================================


def show_legacy_home():

    clear_screen()

    main_frame = ctk.CTkFrame(
        app,
        corner_radius=0
    )

    main_frame.pack(
        fill="both",
        expand=True
    )

    # PHYSILEARN_CM_NAV_GUIDE_V1
    # Keep navigation visible without moving the existing lab cards.
    ctk.CTkButton(
        main_frame,
        text="← Back to Home",
        command=show_home,
        width=165,
        height=38,
        corner_radius=11,
    ).place(x=26, y=20)

    logo = ctk.CTkLabel(
        main_frame,
        text="PhysiLearn",
        font=ctk.CTkFont(
            size=44,
            weight="bold"
        )
    )

    logo.pack(
        pady=(45, 4)
    )

    subtitle = ctk.CTkLabel(
        main_frame,
        text="Turn everyday motion into measurable physics.",
        font=ctk.CTkFont(
            size=19
        )
    )

    subtitle.pack(
        pady=(0, 28)
    )

    mode_label = ctk.CTkLabel(
        main_frame,
        text="CHOOSE A LAB",
        font=ctk.CTkFont(
            size=14,
            weight="bold"
        )
    )

    mode_label.pack(
        pady=(0, 10)
    )

    cards_frame = ctk.CTkFrame(
        main_frame,
        fg_color="transparent"
    )

    cards_frame.pack(
        pady=4
    )

    # -----------------------------------------------------
    # BALL LAB
    # -----------------------------------------------------

    ball_card = ctk.CTkFrame(
        cards_frame,
        width=430,
        height=360,
        corner_radius=25
    )

    ball_card.pack(
        side="left",
        padx=12
    )

    ball_card.pack_propagate(
        False
    )

    ball_badge = ctk.CTkLabel(
        ball_card,
        text="OBJECT MOTION LAB",
        font=ctk.CTkFont(
            size=13,
            weight="bold"
        )
    )

    ball_badge.pack(
        pady=(28, 7)
    )

    ball_title = ctk.CTkLabel(
        ball_card,
        text="Tennis Ball Physics",
        font=ctk.CTkFont(
            size=27,
            weight="bold"
        )
    )

    ball_title.pack(
        pady=(0, 12)
    )

    ball_description = ctk.CTkLabel(
        ball_card,
        text=(
            "Roll a real tennis ball and let PhysiLearn\n"
            "estimate distance, time, speed, displacement,\n"
            "velocity, and acceleration from your webcam."
        ),
        font=ctk.CTkFont(
            size=15
        ),
        justify="center"
    )

    ball_description.pack(
        pady=(0, 15)
    )

    ball_learning = ctk.CTkLabel(
        ball_card,
        text=(
            "Then solve a physics problem using\n"
            "measurements from your own experiment."
        ),
        font=ctk.CTkFont(
            size=14
        ),
        justify="center"
    )

    ball_learning.pack(
        pady=(0, 18)
    )

    ball_button = ctk.CTkButton(
        ball_card,
        text="Open Ball Lab",
        command=show_ball_challenge,
        width=250,
        height=52,
        corner_radius=15,
        font=ctk.CTkFont(
            size=17,
            weight="bold"
        )
    )

    ball_button.pack()

    # -----------------------------------------------------
    # HAND LAB
    # -----------------------------------------------------

    hand_card = ctk.CTkFrame(
        cards_frame,
        width=430,
        height=360,
        corner_radius=25
    )

    hand_card.pack(
        side="left",
        padx=12
    )

    hand_card.pack_propagate(
        False
    )

    hand_badge = ctk.CTkLabel(
        hand_card,
        text="MOTION CHALLENGE",
        font=ctk.CTkFont(
            size=13,
            weight="bold"
        )
    )

    hand_badge.pack(
        pady=(28, 7)
    )

    hand_title = ctk.CTkLabel(
        hand_card,
        text="Constant Velocity",
        font=ctk.CTkFont(
            size=27,
            weight="bold"
        )
    )

    hand_title.pack(
        pady=(0, 12)
    )

    hand_description = ctk.CTkLabel(
        hand_card,
        text=(
            "Move your hand from left to right while\n"
            "PhysiLearn measures direction, velocity\n"
            "variation, and acceleration."
        ),
        font=ctk.CTkFont(
            size=15
        ),
        justify="center"
    )

    hand_description.pack(
        pady=(0, 15)
    )

    hand_learning = ctk.CTkLabel(
        hand_card,
        text=(
            "A rule-based evaluator grades the motion,\n"
            "then the AI Physics Tutor explains it."
        ),
        font=ctk.CTkFont(
            size=14
        ),
        justify="center"
    )

    hand_learning.pack(
        pady=(0, 18)
    )

    hand_button = ctk.CTkButton(
        hand_card,
        text="Open Hand Challenge",
        command=show_challenge,
        width=250,
        height=52,
        corner_radius=15,
        font=ctk.CTkFont(
            size=17,
            weight="bold"
        )
    )

    hand_button.pack()

    footer = ctk.CTkLabel(
        main_frame,
        text=(
            "Computer Vision  •  Physics  •  "
            "AI-Powered Learning"
        ),
        font=ctk.CTkFont(
            size=13
        )
    )

    footer.pack(
        pady=22
    )


# =========================================================

# CHALLENGE SCREEN

# =========================================================



def show_challenge():



    clear_screen()



    challenge_frame = ctk.CTkFrame(

        app,

        corner_radius=0

    )



    challenge_frame.pack(

        fill="both",

        expand=True

    )





    back_button = ctk.CTkButton(

        challenge_frame,

        text="<  Back",

        command=show_home,

        width=100,

        height=40,

        corner_radius=12

    )



    back_button.place(

        x=30,

        y=30

    )





    challenge_number = ctk.CTkLabel(

        challenge_frame,

        text="CHALLENGE 1",

        font=ctk.CTkFont(

            size=14,

            weight="bold"

        )

    )



    challenge_number.pack(

        pady=(35, 5)

    )





    title = ctk.CTkLabel(

        challenge_frame,

        text="Can You Move at Constant Velocity?",

        font=ctk.CTkFont(

            size=34,

            weight="bold"

        )

    )



    title.pack(

        pady=(0, 5)

    )





    subtitle = ctk.CTkLabel(

        challenge_frame,

        text=(

            "Your movement becomes the experiment."

        ),

        font=ctk.CTkFont(

            size=17

        )

    )



    subtitle.pack(

        pady=(0, 15)

    )





    # -----------------------------------------------------

    # MISSION CARD

    # -----------------------------------------------------



    mission_card = ctk.CTkFrame(

        challenge_frame,

        width=700,

        height=390,

        corner_radius=25

    )



    mission_card.pack(

        pady=5

    )



    mission_card.pack_propagate(

        False

    )





    # -----------------------------------------------------

    # YOUR MISSION

    # -----------------------------------------------------



    mission_title = ctk.CTkLabel(

        mission_card,

        text="YOUR MISSION",

        font=ctk.CTkFont(

            size=20,

            weight="bold"

        )

    )



    mission_title.pack(

        pady=(22, 6)

    )





    mission_text = ctk.CTkLabel(

        mission_card,

        text=(

            "Move your hand from left to right while keeping\n"

            "your speed as steady as possible."

        ),

        font=ctk.CTkFont(

            size=17

        ),

        justify="center"

    )



    mission_text.pack(

        pady=(0, 14)

    )





    # -----------------------------------------------------

    # WHAT WE MEASURE

    # -----------------------------------------------------



    analysis_title = ctk.CTkLabel(

        mission_card,

        text="PHYSILEARN WILL MEASURE",

        font=ctk.CTkFont(

            size=15,

            weight="bold"

        )

    )



    analysis_title.pack(

        pady=(0, 5)

    )





    analysis_text = ctk.CTkLabel(

        mission_card,

        text=(

            "Direction  •  Velocity  •  Acceleration"

        ),

        font=ctk.CTkFont(

            size=16

        )

    )



    analysis_text.pack(

        pady=(0, 14)

    )





    # -----------------------------------------------------

    # INSTRUCTIONS

    # -----------------------------------------------------



    instructions_title = ctk.CTkLabel(

        mission_card,

        text="HOW IT WORKS",

        font=ctk.CTkFont(

            size=15,

            weight="bold"

        )

    )



    instructions_title.pack(

        pady=(0, 5)

    )





    instructions = ctk.CTkLabel(

        mission_card,

        text=(

            "1. Keep your hand visible to the webcam.\n"

            "2. Get ready during the 3-second countdown.\n"

            "3. Move smoothly from left to right when recording starts.\n"

            "4. PhysiLearn will stop and analyze your motion automatically."

        ),

        font=ctk.CTkFont(

            size=15

        ),

        justify="left"

    )



    instructions.pack(

        pady=(0, 14)

    )





    # -----------------------------------------------------

    # START BUTTON

    # -----------------------------------------------------



    start_button = ctk.CTkButton(

        mission_card,

        text="Start Challenge",

        command=start_physics_experiment,

        width=300,

        height=55,

        corner_radius=16,

        font=ctk.CTkFont(

            size=18,

            weight="bold"

        )

    )



    start_button.pack(

        pady=(5, 20)

    )





# =========================================================

# PHYSICS EXPERIMENT

# =========================================================



def start_physics_experiment():



    clear_screen()



    loading_frame = ctk.CTkFrame(

        app,

        corner_radius=0

    )



    loading_frame.pack(

        fill="both",

        expand=True

    )





    title = ctk.CTkLabel(

        loading_frame,

        text="Experiment Running",

        font=ctk.CTkFont(

            size=38,

            weight="bold"

        )

    )



    title.pack(

        pady=(170, 15)

    )





    message = ctk.CTkLabel(

        loading_frame,

        text=(

            "Complete the challenge in the webcam window.\n\n"

            "Get ready for the countdown.\n"

            "Recording will start and stop automatically."

        ),

        font=ctk.CTkFont(

            size=18

        ),

        justify="center"

    )



    message.pack(

        pady=20

    )





    progress = ctk.CTkProgressBar(

        loading_frame,

        width=350,

        mode="indeterminate"

    )



    progress.pack(

        pady=25

    )



    progress.start()





    thread = threading.Thread(

        target=run_physics_experiment,

        daemon=True

    )



    thread.start()





def run_physics_experiment():



    script_path = project_file(

        "main.py"

    )



    project_dir = os.path.dirname(

        script_path

    )



    result_path = project_file(

        "experiment_result.json"

    )





    # Delete old result

    if os.path.exists(

        result_path

    ):



        try:

            os.remove(

                result_path

            )



        except OSError:

            pass





    try:



        subprocess.run(

            [

                sys.executable,

                script_path

            ],

            cwd=project_dir

        )



        app.after(

            0,

            load_experiment_result

        )



    except Exception as error:



        print(

            f"Experiment error: {error}"

        )



        app.after(

            0,

            lambda: show_result_error(

                str(error)

            )

        )





# =========================================================

# LOAD RESULT

# =========================================================



def load_experiment_result():



    result_path = project_file(

        "experiment_result.json"

    )



    if not os.path.exists(

        result_path

    ):



        show_result_error(

            "No experiment result was found."

        )



        return





    try:



        with open(

            result_path,

            "r",

            encoding="utf-8"

        ) as file:



            result_data = json.load(

                file

            )





        # Show AI loading screen first.

        show_ai_loading(

            result_data

        )





    except Exception as error:



        show_result_error(

            str(error)

        )





# =========================================================

# AI TUTOR LOADING

# =========================================================



def show_ai_loading(

    result_data

):



    clear_screen()



    loading_frame = ctk.CTkFrame(

        app,

        corner_radius=0

    )



    loading_frame.pack(

        fill="both",

        expand=True

    )





    title = ctk.CTkLabel(

        loading_frame,

        text="Analyzing Your Motion",

        font=ctk.CTkFont(

            size=36,

            weight="bold"

        )

    )



    title.pack(

        pady=(190, 15)

    )





    message = ctk.CTkLabel(

        loading_frame,

        text=(

            "AI Physics Tutor is preparing your explanation..."

        ),

        font=ctk.CTkFont(

            size=18

        )

    )



    message.pack(

        pady=15

    )





    progress = ctk.CTkProgressBar(

        loading_frame,

        width=350,

        mode="indeterminate"

    )



    progress.pack(

        pady=25

    )



    progress.start()





    thread = threading.Thread(

        target=generate_ai_result,

        args=(result_data,),

        daemon=True

    )



    thread.start()





# =========================================================

# GENERATE AI RESULT

# =========================================================



def generate_ai_result(
    result_data
):
    """
    Generate the personalized tutor explanation in a background thread.

    The rule-based evaluator in main.py remains authoritative.
    The AI explains the measurements but does not decide PASS/TRY AGAIN.
    """

    try:

        status = result_data.get(
            "status",
            "TRY_AGAIN"
        )

        # If there was not enough motion data, do not send incomplete
        # measurements to the LLM. Give the student a clear local result.
        if status == "NOT_ENOUGH_DATA":

            result_data["ai_feedback"] = (
                "WHAT HAPPENED\n"
                "PhysiLearn could not collect enough motion data to "
                "evaluate the challenge reliably.\n\n"

                "PHYSICS\n"
                "Velocity describes how position changes over time:\n"
                "v = Δx / Δt\n\n"
                "Acceleration describes how velocity changes over time:\n"
                "a = Δv / Δt\n\n"
                "A useful experiment needs enough position measurements "
                "across time to calculate these changes.\n\n"

                "TRY NEXT\n"
                "Keep your hand clearly visible for the full recording "
                "and move continuously from left to right."
            )

            app.after(
                0,
                lambda: show_results(
                    result_data
                )
            )

            return

        direction_consistency = result_data.get(
            "direction_consistency",
            "N/A"
        )

        velocity_variation = result_data.get(
            "velocity_variation",
            "N/A"
        )

        average_acceleration = result_data.get(
            "average_acceleration",
            "N/A"
        )

        concept = result_data.get(
            "concept",
            (
                "Constant velocity requires both "
                "constant speed and constant direction."
            )
        )

        ai_feedback = generate_tutor_feedback(
            status=status,
            direction_consistency=direction_consistency,
            velocity_variation=velocity_variation,
            average_acceleration=average_acceleration,
            concept=concept
        )

        if not ai_feedback:

            raise ValueError(
                "The AI Tutor returned an empty response."
            )

        result_data[
            "ai_feedback"
        ] = ai_feedback

    except Exception as error:

        print(
            f"AI Tutor error: {error}"
        )

        # -------------------------------------------------
        # APP-LEVEL FALLBACK
        # -------------------------------------------------
        # ai_tutor.py already contains its own fallback.
        # This second fallback keeps the GUI usable even if
        # something unexpected happens before/after the API call.

        feedback = result_data.get(
            "feedback",
            []
        )

        how_to_improve = result_data.get(
            "how_to_improve",
            ""
        )

        happened_text = (
            " ".join(feedback)
            if feedback
            else "PhysiLearn analyzed your motion measurements."
        )

        if not how_to_improve:

            if result_data.get(
                "passed",
                False
            ):

                how_to_improve = (
                    "Repeat the experiment and see if you can make "
                    "your motion even smoother."
                )

            else:

                how_to_improve = (
                    "Move smoothly from left to right at a steady "
                    "speed without reversing direction."
                )

        result_data["ai_feedback"] = (
            "WHAT HAPPENED\n"
            f"{happened_text}\n\n"

            "PHYSICS\n"
            "Velocity describes how position changes over time:\n"
            "v = Δx / Δt\n\n"
            "Acceleration describes how velocity changes over time:\n"
            "a = Δv / Δt\n\n"
            "Constant velocity requires steady speed and steady "
            "direction, so velocity changes very little.\n\n"

            "TRY NEXT\n"
            f"{how_to_improve}"
        )

    app.after(
        0,
        lambda: show_results(
            result_data
        )
    )


# =========================================================

# RESULT SCREEN

# =========================================================



def show_results(
    result_data
):
    """
    Display the experiment measurements and the AI Tutor explanation
    as a compact educational report.
    """

    clear_screen()

    result_frame = ctk.CTkFrame(
        app,
        corner_radius=0
    )

    result_frame.pack(
        fill="both",
        expand=True
    )

    # -----------------------------------------------------
    # RESULT DATA
    # -----------------------------------------------------

    passed = result_data.get(
        "passed",
        False
    )

    status = result_data.get(
        "status",
        "TRY_AGAIN"
    )

    direction_consistency = result_data.get(
        "direction_consistency",
        "N/A"
    )

    velocity_variation = result_data.get(
        "velocity_variation",
        "N/A"
    )

    average_acceleration = result_data.get(
        "average_acceleration",
        "N/A"
    )

    ai_feedback = result_data.get(
        "ai_feedback",
        "Your motion was analyzed successfully."
    )

    ai_sections = parse_ai_sections(
        ai_feedback
    )

    direction_display = format_measurement(
        direction_consistency,
        decimals=1,
        suffix="%"
    )

    variation_display = format_measurement(
        velocity_variation,
        decimals=3
    )

    acceleration_display = format_measurement(
        average_acceleration,
        decimals=3
    )

    # -----------------------------------------------------
    # TITLE
    # -----------------------------------------------------

    title = ctk.CTkLabel(
        result_frame,
        text="Experiment Complete",
        font=ctk.CTkFont(
            size=34,
            weight="bold"
        )
    )

    title.pack(
        pady=(18, 2)
    )

    if status == "NOT_ENOUGH_DATA":

        status_text = "TRY AGAIN"

    elif passed:

        status_text = "PASS"

    else:

        status_text = "TRY AGAIN"

    status_label = ctk.CTkLabel(
        result_frame,
        text=status_text,
        font=ctk.CTkFont(
            size=26,
            weight="bold"
        )
    )

    status_label.pack(
        pady=(0, 8)
    )

    # -----------------------------------------------------
    # MAIN RESULT CARD
    # -----------------------------------------------------

    card = ctk.CTkFrame(
        result_frame,
        width=900,
        height=545,
        corner_radius=24
    )

    card.pack(
        pady=4
    )

    card.pack_propagate(
        False
    )

    motion_title = ctk.CTkLabel(
        card,
        text="YOUR MOTION",
        font=ctk.CTkFont(
            size=17,
            weight="bold"
        )
    )

    motion_title.pack(
        pady=(18, 8)
    )

    # -----------------------------------------------------
    # MEASUREMENT CARDS
    # -----------------------------------------------------

    metrics_frame = ctk.CTkFrame(
        card,
        fg_color="transparent"
    )

    metrics_frame.pack(
        fill="x",
        padx=28,
        pady=(0, 12)
    )

    metric_data = [
        (
            "DIRECTION",
            direction_display,
            "Target ≥ 85%"
        ),
        (
            "VELOCITY VARIATION",
            variation_display,
            "Target < 0.25"
        ),
        (
            "AVG. ACCELERATION",
            acceleration_display,
            "Target < 0.45"
        ),
    ]

    for metric_name, metric_value, metric_target in metric_data:

        metric_card = ctk.CTkFrame(
            metrics_frame,
            height=92,
            corner_radius=16
        )

        metric_card.pack(
            side="left",
            fill="x",
            expand=True,
            padx=6
        )

        metric_card.pack_propagate(
            False
        )

        metric_title = ctk.CTkLabel(
            metric_card,
            text=metric_name,
            font=ctk.CTkFont(
                size=12,
                weight="bold"
            )
        )

        metric_title.pack(
            pady=(11, 1)
        )

        metric_value_label = ctk.CTkLabel(
            metric_card,
            text=metric_value,
            font=ctk.CTkFont(
                size=22,
                weight="bold"
            )
        )

        metric_value_label.pack()

        metric_target_label = ctk.CTkLabel(
            metric_card,
            text=metric_target,
            font=ctk.CTkFont(
                size=11
            )
        )

        metric_target_label.pack(
            pady=(0, 7)
        )

    measurement_note = ctk.CTkLabel(
        card,
        text=(
            "Relative webcam-motion values • "
            "The rule-based evaluator decides PASS / TRY AGAIN"
        ),
        font=ctk.CTkFont(
            size=11
        )
    )

    measurement_note.pack(
        pady=(0, 9)
    )

    # -----------------------------------------------------
    # LEARNING SECTIONS
    # -----------------------------------------------------

    learning_frame = ctk.CTkFrame(
        card,
        fg_color="transparent"
    )

    learning_frame.pack(
        fill="both",
        expand=True,
        padx=34,
        pady=(0, 14)
    )

    left_column = ctk.CTkFrame(
        learning_frame,
        fg_color="transparent"
    )

    left_column.pack(
        side="left",
        fill="both",
        expand=True,
        padx=(0, 7)
    )

    right_column = ctk.CTkFrame(
        learning_frame,
        fg_color="transparent"
    )

    right_column.pack(
        side="left",
        fill="both",
        expand=True,
        padx=(7, 0)
    )

    # WHAT HAPPENED

    happened_card = ctk.CTkFrame(
        left_column,
        corner_radius=16
    )

    happened_card.pack(
        fill="x",
        pady=(0, 10)
    )

    happened_title = ctk.CTkLabel(
        happened_card,
        text="WHAT HAPPENED",
        font=ctk.CTkFont(
            size=14,
            weight="bold"
        )
    )

    happened_title.pack(
        anchor="w",
        padx=18,
        pady=(13, 4)
    )

    happened_text = ctk.CTkLabel(
        happened_card,
        text=ai_sections["WHAT HAPPENED"],
        font=ctk.CTkFont(
            size=13
        ),
        justify="left",
        wraplength=360
    )

    happened_text.pack(
        anchor="w",
        padx=18,
        pady=(0, 14)
    )

    # TRY NEXT

    next_card = ctk.CTkFrame(
        left_column,
        corner_radius=16
    )

    next_card.pack(
        fill="both",
        expand=True
    )

    next_title = ctk.CTkLabel(
        next_card,
        text="TRY NEXT",
        font=ctk.CTkFont(
            size=14,
            weight="bold"
        )
    )

    next_title.pack(
        anchor="w",
        padx=18,
        pady=(13, 4)
    )

    next_text = ctk.CTkLabel(
        next_card,
        text=ai_sections["TRY NEXT"],
        font=ctk.CTkFont(
            size=13
        ),
        justify="left",
        wraplength=360
    )

    next_text.pack(
        anchor="w",
        padx=18,
        pady=(0, 14)
    )

    # PHYSICS

    physics_card = ctk.CTkFrame(
        right_column,
        corner_radius=16
    )

    physics_card.pack(
        fill="both",
        expand=True
    )

    physics_title = ctk.CTkLabel(
        physics_card,
        text="PHYSICS",
        font=ctk.CTkFont(
            size=14,
            weight="bold"
        )
    )

    physics_title.pack(
        anchor="w",
        padx=18,
        pady=(13, 4)
    )

    physics_text = ctk.CTkLabel(
        physics_card,
        text=ai_sections["PHYSICS"],
        font=ctk.CTkFont(
            size=13
        ),
        justify="left",
        wraplength=360
    )

    physics_text.pack(
        anchor="w",
        padx=18,
        pady=(0, 10)
    )

    physics_formula_note = ctk.CTkLabel(
        physics_card,
        text=(
            "Constant velocity → Δv ≈ 0 → acceleration stays low"
        ),
        font=ctk.CTkFont(
            size=12,
            weight="bold"
        ),
        justify="left",
        wraplength=360
    )

    physics_formula_note.pack(
        anchor="w",
        padx=18,
        pady=(0, 14)
    )

    # -----------------------------------------------------
    # BUTTONS
    # -----------------------------------------------------

    button_frame = ctk.CTkFrame(
        result_frame,
        fg_color="transparent"
    )

    button_frame.pack(
        pady=(10, 14)
    )

    retry_button = ctk.CTkButton(
        button_frame,
        text="Try Again",
        command=show_challenge,
        width=190,
        height=46,
        corner_radius=14,
        font=ctk.CTkFont(
            size=16,
            weight="bold"
        )
    )

    retry_button.pack(
        side="left",
        padx=10
    )

    home_button = ctk.CTkButton(
        button_frame,
        text="Back to Home",
        command=show_home,
        width=190,
        height=46,
        corner_radius=14,
        font=ctk.CTkFont(
            size=16,
            weight="bold"
        )
    )

    home_button.pack(
        side="left",
        padx=10
    )


# =========================================================

# BALL PHYSICS LAB

# =========================================================


def show_ball_challenge():

    clear_screen()

    frame = ctk.CTkFrame(
        app,
        corner_radius=0
    )

    frame.pack(
        fill="both",
        expand=True
    )

    back_button = ctk.CTkButton(
        frame,
        text="<  Back",
        command=show_home,
        width=100,
        height=40,
        corner_radius=12
    )

    back_button.place(
        x=30,
        y=30
    )

    lab_label = ctk.CTkLabel(
        frame,
        text="BALL PHYSICS LAB",
        font=ctk.CTkFont(
            size=14,
            weight="bold"
        )
    )

    lab_label.pack(
        pady=(35, 5)
    )

    title = ctk.CTkLabel(
        frame,
        text="Measure a Rolling Tennis Ball",
        font=ctk.CTkFont(
            size=34,
            weight="bold"
        )
    )

    title.pack(
        pady=(0, 5)
    )

    subtitle = ctk.CTkLabel(
        frame,
        text="Create a physics problem from your own real-world motion.",
        font=ctk.CTkFont(
            size=17
        )
    )

    subtitle.pack(
        pady=(0, 15)
    )

    card = ctk.CTkFrame(
        frame,
        width=760,
        height=430,
        corner_radius=25
    )

    card.pack(
        pady=5
    )

    card.pack_propagate(
        False
    )

    mission_title = ctk.CTkLabel(
        card,
        text="YOUR MISSION",
        font=ctk.CTkFont(
            size=20,
            weight="bold"
        )
    )

    mission_title.pack(
        pady=(25, 6)
    )

    mission_text = ctk.CTkLabel(
        card,
        text=(
            "Roll a tennis ball from left to right across a table.\n"
            "Keep the ball roughly the same distance from the webcam."
        ),
        font=ctk.CTkFont(
            size=17
        ),
        justify="center"
    )

    mission_text.pack(
        pady=(0, 15)
    )

    measures_title = ctk.CTkLabel(
        card,
        text="PHYSILEARN WILL ESTIMATE",
        font=ctk.CTkFont(
            size=15,
            weight="bold"
        )
    )

    measures_title.pack(
        pady=(0, 5)
    )

    measures = ctk.CTkLabel(
        card,
        text=(
            "Distance  •  Time  •  Displacement  •  "
            "Speed  •  Velocity  •  Acceleration"
        ),
        font=ctk.CTkFont(
            size=15
        )
    )

    measures.pack(
        pady=(0, 15)
    )

    how_title = ctk.CTkLabel(
        card,
        text="HOW IT WORKS",
        font=ctk.CTkFont(
            size=15,
            weight="bold"
        )
    )

    how_title.pack(
        pady=(0, 5)
    )

    instructions = ctk.CTkLabel(
        card,
        text=(
            "1. Hold the tennis ball still during calibration.\n"
            "2. Get ready during the 3-second countdown.\n"
            "3. Roll the ball left-to-right while recording.\n"
            "4. Close the graph windows after viewing them.\n"
            "5. Use your measured distance and time to calculate average speed."
        ),
        font=ctk.CTkFont(
            size=15
        ),
        justify="left"
    )

    instructions.pack(
        pady=(0, 18)
    )

    accuracy_note = ctk.CTkLabel(
        card,
        text=(
            "Measurements are estimated from webcam calibration using "
            "the tennis ball's known diameter."
        ),
        font=ctk.CTkFont(
            size=12
        ),
        wraplength=650
    )

    accuracy_note.pack(
        pady=(0, 15)
    )

    start_button = ctk.CTkButton(
        card,
        text="Start Ball Experiment",
        command=start_ball_experiment,
        width=300,
        height=55,
        corner_radius=16,
        font=ctk.CTkFont(
            size=18,
            weight="bold"
        )
    )

    start_button.pack()


def start_ball_experiment():

    clear_screen()

    loading_frame = ctk.CTkFrame(
        app,
        corner_radius=0
    )

    loading_frame.pack(
        fill="both",
        expand=True
    )

    title = ctk.CTkLabel(
        loading_frame,
        text="Ball Experiment Running",
        font=ctk.CTkFont(
            size=38,
            weight="bold"
        )
    )

    title.pack(
        pady=(160, 15)
    )

    message = ctk.CTkLabel(
        loading_frame,
        text=(
            "Use the webcam window to complete the experiment.\n\n"
            "Hold the ball still during calibration, then roll it\n"
            "from left to right when recording begins.\n\n"
            "After recording, view and close the graph windows."
        ),
        font=ctk.CTkFont(
            size=18
        ),
        justify="center"
    )

    message.pack(
        pady=20
    )

    progress = ctk.CTkProgressBar(
        loading_frame,
        width=350,
        mode="indeterminate"
    )

    progress.pack(
        pady=25
    )

    progress.start()

    thread = threading.Thread(
        target=run_ball_experiment,
        daemon=True
    )

    thread.start()


def run_ball_experiment():

    script_path = project_file(
        "ball_physics_test.py"
    )

    project_dir = os.path.dirname(
        script_path
    )

    result_path = project_file(
        "ball_experiment_result.json"
    )

    if os.path.exists(
        result_path
    ):

        try:
            os.remove(
                result_path
            )

        except OSError:
            pass

    try:

        completed = subprocess.run(
            [
                sys.executable,
                script_path
            ],
            cwd=project_dir
        )

        if completed.returncode != 0:
            raise RuntimeError(
                "The ball experiment ended before a result was created."
            )

        app.after(
            0,
            load_ball_experiment_result
        )

    except Exception as error:

        print(
            f"Ball experiment error: {error}"
        )

        app.after(
            0,
            lambda: show_ball_error(
                str(error)
            )
        )


def load_ball_experiment_result():

    result_path = project_file(
        "ball_experiment_result.json"
    )

    if not os.path.exists(
        result_path
    ):

        show_ball_error(
            "No ball experiment result was found. "
            "Try the experiment again and keep the ball visible."
        )

        return

    try:

        with open(
            result_path,
            "r",
            encoding="utf-8"
        ) as file:

            result_data = json.load(
                file
            )

        show_ball_learning(
            result_data
        )

    except Exception as error:

        show_ball_error(
            str(error)
        )


def show_ball_learning(
    result_data
):

    clear_screen()

    try:
        distance = float(
            result_data["distance_traveled"]
        )
        displacement = float(
            result_data["horizontal_displacement"]
        )
        motion_time = float(
            result_data["motion_time"]
        )
        average_speed = float(
            result_data["average_speed"]
        )
        average_velocity = float(
            result_data["average_velocity"]
        )
        size_variation = float(
            result_data.get(
                "ball_size_variation_percent",
                0.0
            )
        )

    except (KeyError, TypeError, ValueError) as error:
        show_ball_error(
            f"Ball result data was incomplete: {error}"
        )
        return

    page = ctk.CTkFrame(
        app,
        corner_radius=0
    )

    page.pack(
        fill="both",
        expand=True
    )

    title = ctk.CTkLabel(
        page,
        text="Your Ball Experiment",
        font=ctk.CTkFont(
            size=34,
            weight="bold"
        )
    )

    title.pack(
        pady=(22, 3)
    )

    subtitle = ctk.CTkLabel(
        page,
        text=(
            "PhysiLearn measured the motion. Now use physics to analyze it."
        ),
        font=ctk.CTkFont(
            size=16
        )
    )

    subtitle.pack(
        pady=(0, 14)
    )

    measurements_card = ctk.CTkFrame(
        page,
        width=900,
        height=155,
        corner_radius=22
    )

    measurements_card.pack(
        pady=4
    )

    measurements_card.pack_propagate(
        False
    )

    measured_title = ctk.CTkLabel(
        measurements_card,
        text="MEASURED BY PHYSILEARN",
        font=ctk.CTkFont(
            size=15,
            weight="bold"
        )
    )

    measured_title.pack(
        pady=(16, 9)
    )

    metrics_frame = ctk.CTkFrame(
        measurements_card,
        fg_color="transparent"
    )

    metrics_frame.pack()

    metric_values = [
        (
            "DISTANCE",
            f"{distance:.3f} m"
        ),
        (
            "TIME",
            f"{motion_time:.3f} s"
        ),
        (
            "DISPLACEMENT",
            f"{displacement:+.3f} m"
        ),
    ]

    for metric_name, metric_value in metric_values:

        metric_card = ctk.CTkFrame(
            metrics_frame,
            width=245,
            height=78,
            corner_radius=15
        )

        metric_card.pack(
            side="left",
            padx=8
        )

        metric_card.pack_propagate(
            False
        )

        ctk.CTkLabel(
            metric_card,
            text=metric_name,
            font=ctk.CTkFont(
                size=12,
                weight="bold"
            )
        ).pack(
            pady=(9, 1)
        )

        ctk.CTkLabel(
            metric_card,
            text=metric_value,
            font=ctk.CTkFont(
                size=22,
                weight="bold"
            )
        ).pack()

    challenge_card = ctk.CTkFrame(
        page,
        width=900,
        height=405,
        corner_radius=22
    )

    challenge_card.pack(
        pady=14
    )

    challenge_card.pack_propagate(
        False
    )

    challenge_title = ctk.CTkLabel(
        challenge_card,
        text="CAN YOU CALCULATE THE AVERAGE SPEED?",
        font=ctk.CTkFont(
            size=19,
            weight="bold"
        )
    )

    challenge_title.pack(
        pady=(20, 4)
    )

    question = ctk.CTkLabel(
        challenge_card,
        text=(
            "Use the distance and time measured from your own experiment."
        ),
        font=ctk.CTkFont(
            size=14
        )
    )

    question.pack(
        pady=(0, 8)
    )

    formula = ctk.CTkLabel(
        challenge_card,
        text="v = d / t",
        font=ctk.CTkFont(
            size=28,
            weight="bold"
        )
    )

    formula.pack(
        pady=(0, 12)
    )

    answer_frame = ctk.CTkFrame(
        challenge_card,
        fg_color="transparent"
    )

    answer_frame.pack()

    answer_entry = ctk.CTkEntry(
        answer_frame,
        width=230,
        height=46,
        placeholder_text="Enter average speed",
        justify="center",
        font=ctk.CTkFont(
            size=16
        )
    )

    answer_entry.pack(
        side="left",
        padx=(0, 9)
    )

    ctk.CTkLabel(
        answer_frame,
        text="m/s",
        font=ctk.CTkFont(
            size=16,
            weight="bold"
        )
    ).pack(
        side="left"
    )

    feedback_label = ctk.CTkLabel(
        challenge_card,
        text="",
        font=ctk.CTkFont(
            size=14
        ),
        wraplength=760,
        justify="center"
    )

    feedback_label.pack(
        pady=(12, 2)
    )

    solution_label = ctk.CTkLabel(
        challenge_card,
        text="",
        font=ctk.CTkFont(
            size=14
        ),
        wraplength=760,
        justify="center"
    )

    solution_label.pack(
        pady=(0, 4)
    )

    hint_label = ctk.CTkLabel(
        challenge_card,
        text="",
        font=ctk.CTkFont(
            size=13
        ),
        wraplength=760,
        justify="center"
    )

    hint_label.pack(
        pady=(0, 4)
    )

    attempts = {
        "count": 0
    }

    def show_hint():
        hint_label.configure(
            text=(
                "Hint: average speed = total distance ÷ total time. "
                f"Use {distance:.3f} ÷ {motion_time:.3f}."
            )
        )

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
                text="Enter a number, for example 0.14."
            )
            solution_label.configure(
                text=""
            )
            return

        attempts["count"] += 1

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
                    "Correct! You calculated the speed using "
                    "measurements from your own experiment. "
                    "Continue to the AI Physics Tutor for a personalized explanation."
                )
            )

            ai_button.configure(
                state="normal"
            )

            solution_label.configure(
                text=(
                    f"v = d / t   →   "
                    f"{distance:.3f} / {motion_time:.3f} "
                    f"≈ {average_speed:.3f} m/s\n"
                    f"Average velocity was {average_velocity:+.3f} m/s. "
                    "Speed uses total distance; velocity also includes direction."
                )
            )

            hint_label.configure(
                text=(
                    f"Camera calibration quality: ball-size variation "
                    f"{size_variation:.1f}%. Measurements are estimates."
                )
            )

        else:

            feedback_label.configure(
                text=(
                    "Not quite. Average speed uses total distance divided by time."
                )
            )

            solution_label.configure(
                text=""
            )

            if attempts["count"] >= 2:
                show_hint()

    buttons = ctk.CTkFrame(
        challenge_card,
        fg_color="transparent"
    )

    buttons.pack(
        pady=(8, 5)
    )

    check_button = ctk.CTkButton(
        buttons,
        text="Check Answer",
        command=check_answer,
        width=190,
        height=43,
        corner_radius=13,
        font=ctk.CTkFont(
            size=15,
            weight="bold"
        )
    )

    check_button.pack(
        side="left",
        padx=7
    )

    hint_button = ctk.CTkButton(
        buttons,
        text="Need a Hint?",
        command=show_hint,
        width=170,
        height=43,
        corner_radius=13,
        font=ctk.CTkFont(
            size=15
        )
    )

    hint_button.pack(
        side="left",
        padx=7
    )

    ai_button = ctk.CTkButton(
        buttons,
        text="Continue to AI Tutor",
        command=lambda: show_ball_ai_loading(result_data),
        width=210,
        height=43,
        corner_radius=13,
        font=ctk.CTkFont(
            size=15,
            weight="bold"
        ),
        state="disabled"
    )

    ai_button.pack(
        side="left",
        padx=7
    )

    nav_frame = ctk.CTkFrame(
        page,
        fg_color="transparent"
    )

    nav_frame.pack(
        pady=(0, 12)
    )

    retry_button = ctk.CTkButton(
        nav_frame,
        text="Run Ball Again",
        command=show_ball_challenge,
        width=180,
        height=42,
        corner_radius=13
    )

    retry_button.pack(
        side="left",
        padx=8
    )

    home_button = ctk.CTkButton(
        nav_frame,
        text="Back to Home",
        command=show_home,
        width=180,
        height=42,
        corner_radius=13
    )

    home_button.pack(
        side="left",
        padx=8
    )

    answer_entry.bind(
        "<Return>",
        lambda event: check_answer()
    )

    answer_entry.focus()


def show_ball_ai_loading(result_data):

    clear_screen()

    loading_frame = ctk.CTkFrame(
        app,
        corner_radius=0
    )

    loading_frame.pack(
        fill="both",
        expand=True
    )

    title = ctk.CTkLabel(
        loading_frame,
        text="Connecting Your Experiment to Physics",
        font=ctk.CTkFont(
            size=36,
            weight="bold"
        )
    )

    title.pack(
        pady=(205, 15)
    )

    message = ctk.CTkLabel(
        loading_frame,
        text=(
            "AI Physics Tutor is explaining your real ball measurements...\n"
            "The measurements themselves were calculated by OpenCV and physics code."
        ),
        font=ctk.CTkFont(
            size=17
        ),
        justify="center"
    )

    message.pack(
        pady=15
    )

    progress = ctk.CTkProgressBar(
        loading_frame,
        width=360,
        mode="indeterminate"
    )

    progress.pack(
        pady=25
    )

    progress.start()

    thread = threading.Thread(
        target=generate_ball_ai_result,
        args=(result_data,),
        daemon=True
    )

    thread.start()


def generate_ball_ai_result(result_data):

    try:
        feedback = generate_ball_tutor_feedback(
            distance=result_data.get("distance_traveled"),
            motion_time=result_data.get("motion_time"),
            displacement=result_data.get("horizontal_displacement"),
            average_speed=result_data.get("average_speed"),
            average_velocity=result_data.get("average_velocity"),
            ball_size_variation=result_data.get(
                "ball_size_variation_percent",
                0.0
            ),
        )

        result_data["ball_ai_feedback"] = feedback

    except Exception as error:
        print(
            f"Ball AI Tutor error: {error}"
        )

        result_data["ball_ai_feedback"] = (
            "WHAT HAPPENED\n"
            "PhysiLearn measured your tennis-ball motion successfully.\n\n"
            "PHYSICS CONNECTION\n"
            "Average speed is total distance divided by time: v = d / t. "
            "Velocity uses displacement, so direction matters.\n\n"
            "TRY NEXT\n"
            "Roll the ball back toward its starting point and compare "
            "distance with displacement."
        )

    app.after(
        0,
        lambda: show_ball_ai_result(result_data)
    )


def show_ball_ai_result(result_data):

    clear_screen()

    distance = float(
        result_data.get("distance_traveled", 0.0)
    )
    motion_time = float(
        result_data.get("motion_time", 0.0)
    )
    displacement = float(
        result_data.get("horizontal_displacement", 0.0)
    )
    average_speed = float(
        result_data.get("average_speed", 0.0)
    )
    average_velocity = float(
        result_data.get("average_velocity", 0.0)
    )
    size_variation = float(
        result_data.get("ball_size_variation_percent", 0.0)
    )

    sections = parse_ball_ai_sections(
        result_data.get(
            "ball_ai_feedback",
            ""
        )
    )

    page = ctk.CTkFrame(
        app,
        corner_radius=0
    )

    page.pack(
        fill="both",
        expand=True
    )

    title = ctk.CTkLabel(
        page,
        text="AI Physics Tutor",
        font=ctk.CTkFont(
            size=36,
            weight="bold"
        )
    )

    title.pack(
        pady=(24, 3)
    )

    subtitle = ctk.CTkLabel(
        page,
        text=(
            "Personalized from the measurements in your tennis-ball experiment."
        ),
        font=ctk.CTkFont(
            size=16
        )
    )

    subtitle.pack(
        pady=(0, 12)
    )

    metrics_frame = ctk.CTkFrame(
        page,
        fg_color="transparent"
    )

    metrics_frame.pack(
        pady=(0, 10)
    )

    metric_values = [
        ("DISTANCE", f"{distance:.3f} m"),
        ("TIME", f"{motion_time:.3f} s"),
        ("AVG SPEED", f"{average_speed:.3f} m/s"),
        ("DISPLACEMENT", f"{displacement:+.3f} m"),
    ]

    for name, value in metric_values:
        metric_card = ctk.CTkFrame(
            metrics_frame,
            width=205,
            height=72,
            corner_radius=14
        )

        metric_card.pack(
            side="left",
            padx=6
        )

        metric_card.pack_propagate(False)

        ctk.CTkLabel(
            metric_card,
            text=name,
            font=ctk.CTkFont(
                size=11,
                weight="bold"
            )
        ).pack(
            pady=(9, 1)
        )

        ctk.CTkLabel(
            metric_card,
            text=value,
            font=ctk.CTkFont(
                size=19,
                weight="bold"
            )
        ).pack()

    tutor_card = ctk.CTkFrame(
        page,
        width=920,
        height=445,
        corner_radius=22
    )

    tutor_card.pack(
        pady=5
    )

    tutor_card.pack_propagate(False)

    section_specs = [
        ("WHAT HAPPENED", sections["WHAT HAPPENED"]),
        ("PHYSICS CONNECTION", sections["PHYSICS CONNECTION"]),
        ("TRY NEXT", sections["TRY NEXT"]),
    ]

    for index, (heading, body) in enumerate(section_specs):
        ctk.CTkLabel(
            tutor_card,
            text=heading,
            font=ctk.CTkFont(
                size=15,
                weight="bold"
            ),
            anchor="w"
        ).pack(
            fill="x",
            padx=40,
            pady=((20 if index == 0 else 11), 3)
        )

        ctk.CTkLabel(
            tutor_card,
            text=body,
            font=ctk.CTkFont(
                size=14
            ),
            justify="left",
            anchor="w",
            wraplength=830
        ).pack(
            fill="x",
            padx=40
        )

    note_text = (
        f"Estimated camera-based measurements • Avg velocity: "
        f"{average_velocity:+.3f} m/s • Ball-size variation: "
        f"{size_variation:.1f}%"
    )

    ctk.CTkLabel(
        page,
        text=note_text,
        font=ctk.CTkFont(
            size=12
        )
    ).pack(
        pady=(7, 6)
    )

    nav_frame = ctk.CTkFrame(
        page,
        fg_color="transparent"
    )

    nav_frame.pack(
        pady=(0, 10)
    )

    ctk.CTkButton(
        nav_frame,
        text="Run Ball Again",
        command=show_ball_challenge,
        width=180,
        height=42,
        corner_radius=13
    ).pack(
        side="left",
        padx=8
    )

    ctk.CTkButton(
        nav_frame,
        text="Back to Home",
        command=show_home,
        width=180,
        height=42,
        corner_radius=13
    ).pack(
        side="left",
        padx=8
    )


def show_ball_error(
    error_message
):

    clear_screen()

    frame = ctk.CTkFrame(
        app,
        corner_radius=0
    )

    frame.pack(
        fill="both",
        expand=True
    )

    title = ctk.CTkLabel(
        frame,
        text="Ball Experiment Error",
        font=ctk.CTkFont(
            size=32,
            weight="bold"
        )
    )

    title.pack(
        pady=(180, 20)
    )

    message = ctk.CTkLabel(
        frame,
        text=error_message,
        font=ctk.CTkFont(
            size=17
        ),
        wraplength=700
    )

    message.pack(
        pady=10
    )

    buttons = ctk.CTkFrame(
        frame,
        fg_color="transparent"
    )

    buttons.pack(
        pady=25
    )

    retry = ctk.CTkButton(
        buttons,
        text="Try Ball Lab Again",
        command=show_ball_challenge,
        width=190,
        height=45
    )

    retry.pack(
        side="left",
        padx=8
    )

    home = ctk.CTkButton(
        buttons,
        text="Back to Home",
        command=show_home,
        width=180,
        height=45
    )

    home.pack(
        side="left",
        padx=8
    )


# =========================================================

# ERROR SCREEN

# =========================================================



def show_result_error(

    error_message

):



    clear_screen()



    error_frame = ctk.CTkFrame(

        app,

        corner_radius=0

    )



    error_frame.pack(

        fill="both",

        expand=True

    )





    title = ctk.CTkLabel(

        error_frame,

        text="Experiment Result Error",

        font=ctk.CTkFont(

            size=32,

            weight="bold"

        )

    )



    title.pack(

        pady=(180, 20)

    )





    message = ctk.CTkLabel(

        error_frame,

        text=error_message,

        font=ctk.CTkFont(

            size=17

        ),

        wraplength=650

    )



    message.pack(

        pady=10

    )





    back_button = ctk.CTkButton(

        error_frame,

        text="Back",

        command=show_challenge,

        width=180,

        height=45

    )



    back_button.pack(

        pady=25

    )





# =========================================================

# START APP

# =========================================================




# =========================================================
# EUREKADEV 2.0 HOME SCREEN
# Keeps the original lab functions and original home screen.
# =========================================================

_eureka_children = []


def _eureka_launch(script_name):
    """Open each interactive lab in a separate Windows console."""
    from pathlib import Path
    import subprocess
    import sys

    project = Path(__file__).resolve().parent
    script = project / script_name
    if not script.is_file():
        _eureka_status.configure(text=f"File not found: {script_name}")
        return

    try:
        # A console is necessary because Object Lab / Compare Lab ask for input.
        # /k keeps the results visible after the script finishes.
        if sys.platform == "win32":
            command = subprocess.list2cmdline([sys.executable, str(script)])
            process = subprocess.Popen(
                ["cmd.exe", "/k", command],
                cwd=str(project),
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
        else:
            # Non-Windows fallback: scripts are interactive in the parent console.
            process = subprocess.Popen(
                [sys.executable, str(script)], cwd=str(project)
            )
        _eureka_children.append(process)
        _eureka_status.configure(text=f"Launched {script_name}. Close its camera/console when done.")
    except Exception as exc:
        _eureka_status.configure(text=f"Cannot launch {script_name}: {exc}")


# =========================================================
# OBJECT PICKER (EUREKADEV)
# Choose in the app, then launch the tracker with --object.
# No console input is required. Original labs remain unchanged.
# =========================================================

def show_object_picker():
    """Choose a familiar object, then run the same physics measurements."""
    clear_screen()

    page = ctk.CTkScrollableFrame(app, fg_color="transparent")
    page.pack(fill="both", expand=True, padx=36, pady=12)

    header = ctk.CTkFrame(page, fg_color="transparent")
    header.pack(fill="x", pady=(0, 5))
    ctk.CTkButton(
        header, text="<  Back to Home", width=155, height=38,
        corner_radius=12, command=show_home
    ).pack(side="left")

    ctk.CTkLabel(
        page, text="Object Physics Lab",
        font=ctk.CTkFont(size=34, weight="bold")
    ).pack(pady=(6, 3))
    ctk.CTkLabel(
        page, text="Choose any available object",
        font=ctk.CTkFont(size=16), text_color=("gray40", "gray75")
    ).pack(pady=(0, 18))

    # Each choice uses the SAME measurement and tracking pipeline.
    options = [
        ("1", "Toy Car", "🚗"),
        ("2", "Box", "📦"),
        ("3", "Tennis Ball", "🎾"),
        ("4", "Custom Object", "🎯"),
    ]
    choice = {"code": "1", "name": "Toy Car"}
    buttons = {}

    cards = ctk.CTkFrame(page, fg_color="transparent")
    cards.pack(fill="x", padx=26)
    cards.grid_columnconfigure((0, 1), weight=1, uniform="objects")

    def pick_object(key, name):
        choice.update(code=key, name=name)
        for label, button in buttons.items():
            button.configure(
                fg_color=("#24578A", "#24578A") if label == name
                else ("gray83", "gray28"),
                hover_color=("#1C4975", "#1C4975") if label == name
                else ("gray75", "gray34"),
                text_color="white" if label == name else ("gray15", "white")
            )
        selection_label.configure(text=f"Selected: {name}")

    for index, (key, name, emoji) in enumerate(options):
        button = ctk.CTkButton(
            cards, text=f"{emoji}   {name}", height=88, corner_radius=17,
            font=ctk.CTkFont(size=21, weight="bold"),
            command=lambda k=key, n=name: pick_object(k, n)
        )
        button.grid(row=index // 2, column=index % 2, padx=10, pady=9, sticky="ew")
        buttons[name] = button

    common = ctk.CTkFrame(page, corner_radius=18)
    common.pack(fill="x", padx=36, pady=(18, 10))
    selection_label = ctk.CTkLabel(
        common, text="Selected: Toy Car",
        font=ctk.CTkFont(size=18, weight="bold")
    )
    selection_label.pack(pady=(15, 3))
    ctk.CTkLabel(
        common, text="Measurements available for every object",
        font=ctk.CTkFont(size=15)
    ).pack(pady=(0, 6))

    measures = ctk.CTkFrame(common, fg_color="transparent")
    measures.pack(fill="x", padx=30, pady=(0, 4))
    measures.grid_columnconfigure((0, 1), weight=1)
    for i, metric in enumerate(("Distance", "Displacement", "Time", "Average Speed")):
        ctk.CTkLabel(
            measures, text="✓  " + metric, font=ctk.CTkFont(size=15)
        ).grid(row=i // 2, column=i % 2, sticky="w", padx=18, pady=4)

    # A ruler is required for true centimeter measurements; never relabel pixels as cm.
    cm_hint = ctk.CTkFrame(common, corner_radius=12,
                           fg_color=("#e7f1fc", "#243548"))
    cm_hint.pack(fill="x", padx=22, pady=(7, 14))
    ctk.CTkLabel(
        cm_hint, text="📏  Want centimeters instead of pixels?",
        font=ctk.CTkFont(size=14, weight="bold"),
        anchor="w", text_color=("#18558c", "#91caff")
    ).pack(fill="x", padx=18, pady=(12, 4))
    ctk.CTkLabel(
        cm_hint,
        text=("Place a real 25 cm ruler on the same surface as your object. "
              "In the camera: press 3 (Ruler), click the 0 cm and 25 cm marks, "
              "then press 1 (Select) and 4 (Record). "
              "Results and graphs will use cm and cm/s after calibration."),
        font=ctk.CTkFont(size=13), justify="left", anchor="w",
        wraplength=850, text_color=("#29445c", "#e1eaf5")
    ).pack(fill="x", padx=18, pady=(0, 6))
    ctk.CTkLabel(
        cm_hint,
        text="No ruler? Pixel mode still works; press 5 in the camera to return to px.",
        font=ctk.CTkFont(size=12), justify="left", anchor="w",
        wraplength=850, text_color=("#52687b", "#bbcedf")
    ).pack(fill="x", padx=18, pady=(0, 12))

    status = ctk.CTkLabel(
        page,
        text="Camera keys: 3 ruler calibration · 1 select · 4 record/stop · 5 pixels · 2 quit.",
        font=ctk.CTkFont(size=13),
        text_color=("gray40", "gray75"), wraplength=860
    )

    def start_object():
        launch_new_eureka_experiment("object", choice["code"], choice["name"], status)

    ctk.CTkButton(
        page, text="Start Experiment", width=270, height=48,
        font=ctk.CTkFont(size=17, weight="bold"),
        corner_radius=14, command=start_object
    ).pack(pady=(2, 7))
    status.pack(pady=(2, 15))
    pick_object("1", "Toy Car")


# =========================================================
# EUREKA EXPERIMENT VIEWER + OPTIONAL GROUNDED AI TUTOR
# =========================================================

def show_ramp_launcher():
    """Ramp Lab introduction; existing camera and analysis pipeline untouched."""
    # PHYSILEARN_RAMP_LAUNCHER_POLISH_V1
    clear_screen()

    page = ctk.CTkFrame(app, fg_color="transparent")
    page.pack(fill="both", expand=True, padx=42, pady=20)

    ctk.CTkButton(
        page, text="← Back to Home", width=170, height=38,
        command=show_home
    ).pack(anchor="w", pady=(0, 16))

    ctk.CTkLabel(
        page, text="Ramp Physics Lab",
        font=ctk.CTkFont(size=34, weight="bold")
    ).pack(pady=(0, 3))
    ctk.CTkLabel(
        page, text="Explore how a toy car moves along an inclined surface",
        font=ctk.CTkFont(size=15),
        text_color=("gray40", "gray75")
    ).pack(pady=(0, 19))

    content = ctk.CTkFrame(page, fg_color="transparent")
    content.pack(fill="x", padx=24)
    content.grid_columnconfigure((0, 1), weight=1, uniform="ramp_columns")

    investigate = ctk.CTkFrame(content, corner_radius=16)
    investigate.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 12))
    ctk.CTkLabel(
        investigate, text="WHAT YOU'LL INVESTIGATE",
        font=ctk.CTkFont(size=14, weight="bold"), anchor="w",
        text_color=("#245f91", "#8bc9ff")
    ).pack(fill="x", padx=22, pady=(17, 10))
    for item in (
        "• Position and displacement along the ramp",
        "• How estimated speed changes during the run",
        "• How gravity and friction may affect motion",
    ):
        ctk.CTkLabel(
            investigate, text=item, font=ctk.CTkFont(size=13),
            anchor="w", justify="left", wraplength=440
        ).pack(fill="x", padx=22, pady=(0, 9))
    ctk.CTkLabel(investigate, text="", height=2).pack(pady=(0, 2))

    setup = ctk.CTkFrame(content, corner_radius=16)
    setup.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 12))
    ctk.CTkLabel(
        setup, text="EXPERIMENT SETUP",
        font=ctk.CTkFont(size=14, weight="bold"), anchor="w",
        text_color=("#245f91", "#8bc9ff")
    ).pack(fill="x", padx=22, pady=(17, 9))
    for key, instruction in (
        ("3", "Mark the direction of the ramp"),
        ("1", "Select the toy car in the camera"),
        ("4", "Start recording, then stop with 4"),
        ("2", "Close camera to review the results"),
    ):
        line = ctk.CTkFrame(setup, fg_color="transparent")
        line.pack(fill="x", padx=21, pady=(0, 7))
        ctk.CTkLabel(
            line, text=key, width=30, height=26, corner_radius=8,
            fg_color=("#dceeff", "#205780"),
            text_color=("#16446d", "white"),
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(
            line, text=instruction, font=ctk.CTkFont(size=13),
            anchor="w", justify="left", wraplength=365
        ).pack(side="left", fill="x", expand=True)

    status = ctk.CTkLabel(
        page, text="Ready to open camera", font=ctk.CTkFont(size=13),
        text_color=("gray40", "gray75"), wraplength=920
    )
    ctk.CTkButton(
        page, text="Start Ramp Experiment  →", width=290, height=47,
        corner_radius=12, font=ctk.CTkFont(size=16, weight="bold"),
        command=lambda: launch_new_eureka_experiment("ramp", None, "Ramp", status)
    ).pack(pady=(0, 6))
    status.pack(pady=(0, 10))


def launch_new_eureka_experiment(lab, object_code, object_name, status):
    """Launch OpenCV and show the new recording in CTk after the camera exits."""
    from pathlib import Path
    project = Path(__file__).resolve().parent
    if lab == "object":
        script = project / "object_physics_lab_v2.py"
        files_dir = project / "experiments"
        command = [sys.executable, str(script), "--object", object_code]
        matching = lambda p: p.name.endswith((
            "_toy_car.json" if object_code == "1" else
            "_box.json" if object_code == "2" else
            "_tennis_ball.json" if object_code == "3" else
            "_custom_object.json"
        ))
    else:
        script = project / "ramp_physics_lab_v2.py"
        files_dir = project / "experiments" / "ramp"
        command = [sys.executable, str(script)]
        matching = lambda p: p.name.startswith("ramp_v2_") and p.suffix == ".json"

    if not script.is_file():
        status.configure(text=f"Missing {script.name}")
        return

    files_dir.mkdir(parents=True, exist_ok=True)
    old_files = {str(p.resolve()) for p in files_dir.glob("*.json")}
    log_dir = project / "logs"
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / f"{lab}_lab.log"
    try:
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        with log_path.open("a", encoding="utf-8") as log:
            log.write(f"\n--- Starting {object_name} ---\n")
            proc = subprocess.Popen(
                command, cwd=str(project), stdin=subprocess.DEVNULL,
                stdout=log, stderr=subprocess.STDOUT, creationflags=flags
            )
        _eureka_children.append(proc)
    except Exception as exc:
        status.configure(text=f"Could not start experiment: {exc}")
        return

    status.configure(text=f"Camera open for {object_name}. Record with 4, then exit with 2 to view results. F toggles fullscreen.")

    def check_done():
        # The user might go back to Home while the camera is open.
        try:
            visible = bool(status.winfo_exists())
        except Exception:
            visible = False
        code = proc.poll()
        if code is None:
            app.after(700, check_done)
            return
        if not visible:
            return
        new_files = [p for p in files_dir.glob("*.json")
                     if str(p.resolve()) not in old_files and matching(p)]
        if new_files:
            newest = max(new_files, key=lambda p: p.stat().st_mtime_ns)
            try:
                result = json.loads(newest.read_text(encoding="utf-8"))
                show_eureka_results(lab, result, newest.with_suffix(".png"))
            except (OSError, ValueError) as exc:
                status.configure(text=f"Recording saved, but could not open results: {exc}")
        elif code != 0:
            status.configure(text=f"Experiment failed (exit {code}). Read logs/{lab}_lab.log.")
        else:
            status.configure(text="Camera closed. No recording saved. Press 4 again to stop before exiting.")

    app.after(700, check_done)


def _sections_of_explanation(text):
    """Read both plain and Markdown-formatted AI headings safely."""
    import re

    sections = {"WHAT HAPPENED": [], "PHYSICS": [], "TRY NEXT": []}
    active = None
    for raw in str(text).splitlines():
        line = raw.strip()
        if not line:
            continue
        # Models may format headings as ### WHAT HAPPENED or **PHYSICS**.
        cleaned = re.sub(r"^#{1,6}\s*", "", line)
        cleaned = re.sub(r"^\d+[.)]\s*", "", cleaned)
        cleaned = cleaned.strip(" *`_#-—")
        heading, separator, same_line_text = cleaned.partition(":")
        candidate = heading.strip(" *`_#-—").upper()
        if candidate in sections:
            active = candidate
            if separator and same_line_text.strip():
                sections[active].append(same_line_text.strip())
            continue
        if active is not None:
            sections[active].append(line)

    result = {heading: " ".join(lines).strip() for heading, lines in sections.items()}
    # Never hide a valid AI answer behind three "No explanation available" labels.
    if not any(result.values()) and str(text).strip():
        result["WHAT HAPPENED"] = str(text).strip()
    return result


def show_eureka_results(lab, result, graph_file):
    """PHYSILEARN_SMOOTH_RESULTS_CANVAS_V1 — smooth, read-only native Canvas."""
    import tkinter as tk
    from tkinter import font as tkfont
    from pathlib import Path
    from PIL import Image, ImageTk
    from eureka_ai_tutor import local_explanation

    clear_screen()
    dark = ctk.get_appearance_mode().lower() != 'light'
    background = '#242424' if dark else '#f7f8fa'
    foreground = '#f1f3f8' if dark else '#202938'
    muted = '#b2bdcd' if dark else '#536175'
    card_bg = '#303030' if dark else '#ecf0f4'
    accent = '#79bdff' if dark else '#116caf'

    graph_file = Path(graph_file)
    back_command = show_object_picker if lab == 'object' else show_ramp_launcher

    # Fixed navigation means no button widgets need to move during scroll.
    nav = ctk.CTkFrame(app, fg_color='transparent')
    nav.pack(fill='x', padx=32, pady=(13, 8))
    ctk.CTkButton(nav, text='← Back to Lab', width=145, height=39,
                  command=back_command).pack(side='left')
    ctk.CTkButton(nav, text='Explain with AI  →', width=192, height=39,
                  command=lambda: show_eureka_ai_deep_dive(lab, result, graph_file)
                  ).pack(side='right', padx=(10, 0))
    ctk.CTkButton(nav, text='Home', width=100, height=39,
                  fg_color=('#d7e2ec', '#383b45'),
                  text_color=('#202938', '#f1f3f8'),
                  hover_color=('#c5d3e0', '#484c58'),
                  command=show_home).pack(side='right')

    container = ctk.CTkFrame(app, fg_color='transparent')
    container.pack(fill='both', expand=True, padx=(22, 12), pady=(0, 12))
    canvas = tk.Canvas(container, bg=background, borderwidth=0,
                       highlightthickness=0, yscrollincrement=36)
    scrollbar = ctk.CTkScrollbar(container, command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side='right', fill='y', padx=(4, 0))
    canvas.pack(side='left', fill='both', expand=True)

    title_font = tkfont.Font(family='Segoe UI', size=25, weight='bold')
    section_font = tkfont.Font(family='Segoe UI', size=19, weight='bold')
    heading_font = tkfont.Font(family='Segoe UI', size=11, weight='bold')
    body_font = tkfont.Font(family='Segoe UI', size=12)
    number_font = tkfont.Font(family='Segoe UI', size=20, weight='bold')
    caption_font = tkfont.Font(family='Segoe UI', size=10)

    if lab == 'object':
        unit = result.get('measurement_units', 'px')
        if unit not in ('cm', 'px'):
            unit = 'px'
        metrics = [
            ('DISTANCE', result.get('distance'), unit),
            ('DISPLACEMENT', result.get('displacement_magnitude'), unit),
            ('RECORDING TIME', result.get('duration_s'), 's'),
            ('AVERAGE SPEED', result.get('average_speed'), unit + '/s'),
        ]
    else:
        metrics = [
            ('RAMP PATH', result.get('approx_along_ramp_path_px'), 'px'),
            ('DISPLACEMENT', result.get('along_ramp_displacement_px'), 'px'),
            ('RECORDING TIME', result.get('duration_s'), 's'),
            ('PEAK VELOCITY (EST.)', result.get('peak_downhill_velocity_px_s'), 'px/s'),
        ]

    # Local summary is calculated once — no AI network calls on this page.
    explanation_parts = _sections_of_explanation(local_explanation(lab, result))
    note = ('Values depend on camera calibration and tracking accuracy.'
            if lab == 'object' and result.get('calibration_used') else
            'Image pixels are NOT centimeters; camera geometry and tracking noise affect accuracy.')

    # Resizing the image is done ONCE. Scrolling only moves one Canvas image.
    image_ref = {'photo': None, 'error': None}
    if graph_file.is_file():
        try:
            with Image.open(graph_file) as source_image:
                graph = source_image.convert('RGB')
                target_width = min(845, graph.width)
                if graph.width != target_width:
                    target_height = max(1, round(graph.height * target_width / graph.width))
                    graph = graph.resize((target_width, target_height), Image.Resampling.LANCZOS)
                image_ref['photo'] = ImageTk.PhotoImage(graph, master=canvas)
        except Exception as exc:
            image_ref['error'] = 'Could not display saved graph (' + type(exc).__name__ + ').'
    else:
        image_ref['error'] = 'Graph file not found; measurements are still available.'

    redraw_job = {'id': None}
    last_width = {'value': 0}

    def render():
        if not canvas.winfo_exists():
            return
        previous_position = canvas.yview()[0]
        width = max(440, canvas.winfo_width())
        content_width = min(1140, max(360, width - 70))
        left = max(22, (width - content_width) / 2)
        right = left + content_width
        middle = (left + right) / 2
        canvas.delete('all')
        y = 12.0

        def text_at(x, y0, value, font, color=foreground, wrap=None, anchor='nw', justify='left'):
            item = canvas.create_text(x, y0, text=str(value), font=font, fill=color,
                                      width=wrap, anchor=anchor, justify=justify)
            bounds = canvas.bbox(item)
            return float(bounds[3] - bounds[1]) if bounds else 20.0

        def center(value, font, color=foreground, gap=8):
            nonlocal y
            h = text_at(middle, y, value, font, color, content_width - 12,
                        anchor='n', justify='center')
            y += h + gap

        def metric_card(x1, x2, y1, label, value, unit):
            # One rectangle and two strings rather than nested CustomTkinter frames.
            canvas.create_rectangle(x1, y1, x2, y1 + 94, fill=card_bg,
                                    outline=card_bg)
            text_at((x1+x2)/2, y1+17, label, heading_font, muted,
                    max(100, x2-x1-30), anchor='n', justify='center')
            try:
                formatted = f'{float(value):.2f} {unit}'
            except (TypeError, ValueError):
                formatted = 'N/A'
            text_at((x1+x2)/2, y1+43, formatted, number_font, foreground,
                    max(100, x2-x1-30), anchor='n', justify='center')

        def summary_card(heading, body):
            nonlocal y
            y_start = y
            body = body if body else 'No explanation available.'
            inside_width = content_width - 44
            y += 18
            y += text_at(left+22, y, heading, heading_font, accent, inside_width) + 10
            y += text_at(left+22, y, body, body_font, foreground, inside_width) + 21
            box = canvas.create_rectangle(left, y_start, right, y,
                                          fill=card_bg, outline=card_bg)
            canvas.tag_lower(box)
            y += 9

        title = (str(result.get('object_name', 'Object')) + ' — Experiment Results'
                 if lab == 'object' else 'Ramp — Experiment Results')
        center(title, title_font, gap=7)
        center('Saved webcam measurements and physics explanation', body_font, muted, gap=22)
        gutter = 14
        half = (content_width - gutter) / 2
        for i, (label, value, unit) in enumerate(metrics):
            x = left if i % 2 == 0 else left + half + gutter
            yy = y + (i//2)*106
            metric_card(x, x + half, yy, label, value, unit)
        y += 2*106 + 14

        center('Motion graphs', section_font, gap=12)
        if image_ref['photo'] is not None:
            photo = image_ref['photo']
            graph_x = middle
            canvas.create_image(graph_x, y, image=photo, anchor='n')
            y += photo.height() + 12
        else:
            y += text_at(left+16, y, image_ref['error'] or 'Graph unavailable.',
                         body_font, muted, content_width-32) + 18
        y += text_at(left+10, y, note, caption_font, muted, content_width-20) + 25

        center('Physics Tutor · Quick Summary', section_font, gap=14)
        for heading in ('WHAT HAPPENED', 'PHYSICS', 'TRY NEXT'):
            summary_card(heading, explanation_parts.get(heading, ''))
        y += 12
        center('For Motion Analysis, formulas and AI explanations, choose “Explain with AI” above.',
               caption_font, muted, gap=25)
        canvas.configure(scrollregion=(0, 0, width, max(y, canvas.winfo_height())))
        canvas.yview_moveto(previous_position)

    # Canvas isn't recreated when the mouse wheel moves. Only window resizes
    # schedule a draw, and rapid resize events are debounced.
    def resize(event):
        if abs(event.width - last_width['value']) < 12:
            return
        last_width['value'] = event.width
        if redraw_job['id'] is not None:
            try:
                canvas.after_cancel(redraw_job['id'])
            except tk.TclError:
                pass
        redraw_job['id'] = canvas.after(135, render)

    def wheel(event):
        if not canvas.winfo_exists():
            return 'break'
        ticks = max(-6, min(6, round(event.delta / 120)))
        if not ticks and event.delta:
            ticks = 1 if event.delta > 0 else -1
        canvas.yview_scroll(-ticks * 2, 'units')
        return 'break'

    canvas.bind('<Configure>', resize)
    canvas.bind('<MouseWheel>', wheel)
    canvas.bind('<Button-4>', lambda e: (canvas.yview_scroll(-2, 'units'), 'break')[1])
    canvas.bind('<Button-5>', lambda e: (canvas.yview_scroll(2, 'units'), 'break')[1])
    canvas.after(150, render)


def show_eureka_ai_deep_dive(lab, result, graph_file):
    """PHYSILEARN_SMOOTH_DEEP_DIVE_V1: one native Canvas, no nested scrollable cards."""
    import tkinter as tk
    from tkinter import font as tkfont
    import queue
    import threading
    from eureka_motion_story import explain_story_with_ai, parse_story_sections  # PHYSILEARN_AI_MOTION_STORY_V1
    from eureka_motion_analysis import build_motion_report, build_formula_cards
    from eureka_physics_principle import choose_physics_principle  # PHYSILEARN_PHYSICS_PRINCIPLE_V1

    clear_screen()
    dark = ctk.get_appearance_mode().lower() != "light"
    background = "#242424" if dark else "#f7f8fa"
    foreground = "#f1f3f8" if dark else "#202938"
    secondary = "#b2bdcd" if dark else "#536175"
    card_color = "#292d36" if dark else "#e8eef6"
    card_secondary = "#303030" if dark else "#f0f2f6"
    accent = "#79bdff" if dark else "#116caf"
    warning = "#ffcd82" if dark else "#8c5400"

    top = ctk.CTkFrame(app, fg_color="transparent")
    top.pack(fill="x", padx=35, pady=(14, 9))
    ctk.CTkButton(top, text="← Back to Results", width=185, height=38,
                  command=lambda: show_eureka_results(lab, result, graph_file)).pack(side="left")
    status_text = ctk.CTkLabel(top, text="Generating explanation…",
                               font=ctk.CTkFont(size=12), text_color=("gray35", "gray75"))
    status_text.pack(side="right", padx=8)

    # A native Tk Canvas draws the entire report; scrolling moves a single canvas
    # rather than asking dozens of CustomTkinter labels/frames to redraw.
    container = ctk.CTkFrame(app, fg_color="transparent")
    container.pack(fill="both", expand=True, padx=(25, 15), pady=(0, 12))
    canvas = tk.Canvas(container, bg=background, highlightthickness=0,
                       borderwidth=0, relief="flat", yscrollincrement=32)
    scrollbar = ctk.CTkScrollbar(container, command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y", padx=(3, 0))
    canvas.pack(side="left", fill="both", expand=True)

    title_font = tkfont.Font(family="Segoe UI", size=25, weight="bold")
    section_font = tkfont.Font(family="Segoe UI", size=20, weight="bold")
    heading_font = tkfont.Font(family="Segoe UI", size=12, weight="bold")
    body_font = tkfont.Font(family="Segoe UI", size=12)
    caption_font = tkfont.Font(family="Segoe UI", size=10)
    numeric_font = tkfont.Font(family="Segoe UI", size=14, weight="bold")

    report = build_motion_report(lab, result)
    formulas = build_formula_cards(lab, result)
    parts = {"HOW IT MOVED": "Observing your recorded motion…",
             "WHY IT CHANGED": "Waiting for explanation…",
             "PHYSICS BEHIND IT": "Waiting for physics interpretation…",
             "WHAT WE LEARNED": "Waiting for the experiment takeaway…"}
    state = {"parts": parts, "source": None}
    redraw_id = {"value": None}

    def draw(preserve=True):
        if not canvas.winfo_exists():
            return
        view_fraction = canvas.yview()[0] if preserve else 0.0
        canvas.delete("all")
        width = max(340, canvas.winfo_width())
        content_width = min(1150, max(285, width - 68))
        left = max(18, (width - content_width) / 2)
        right = left + content_width
        y = 12.0

        def put(x, y0, string, font, color, max_width=None):
            item = canvas.create_text(x, y0, text=str(string), fill=color, font=font,
                                      anchor="nw", justify="left", width=max_width)
            bbox = canvas.bbox(item)
            return float(bbox[3] - bbox[1]) if bbox else 22.0

        def center(text, font, color, space_after=8):
            nonlocal y
            item = canvas.create_text((left + right) / 2, y, text=str(text), fill=color,
                                      font=font, anchor="n", justify="center",
                                      width=content_width)
            bbox = canvas.bbox(item)
            y += (bbox[3] - bbox[1] if bbox else 32) + space_after

        def card(number, title, subtitle, body, background_color, emphasis=False):
            nonlocal y
            y_start = y
            x = left + 20
            inside_width = max(220, content_width - 40)
            y += 18
            small = (str(number) + "   ") if number else ""
            y += put(x, y, small + title, heading_font, accent if emphasis else foreground,
                     inside_width) + 7
            if subtitle:
                y += put(x, y, subtitle, caption_font, secondary, inside_width) + 12
            y += put(x, y, body, body_font, foreground, inside_width) + 22
            rectangle = canvas.create_rectangle(left, y_start, right, y, fill=background_color,
                                                outline=("#394454" if emphasis and dark else background_color),
                                                width=1)
            canvas.tag_lower(rectangle)
            y += 11

        title = (result.get("object_name", "Object") if lab == "object" else "Ramp")
        center("AI Physics Deep Dive", title_font, foreground, 6)
        center(str(title) + " · Based on recorded measurements", body_font, secondary, 21)
        center("AI Motion Insight", section_font, foreground, 8)
        section_defs = (
            ("01", "HOW IT MOVED", "What the measurements show", "HOW IT MOVED"),
            ("02", "WHY IT CHANGED", "Possible explanations — not proven causes", "WHY IT CHANGED"),
            ("03", "PHYSICS BEHIND IT", "What the numbers mean", "PHYSICS BEHIND IT"),
            ("04", "WHAT WE LEARNED", "One takeaway and the next test", "WHAT WE LEARNED"),
        )
        for num, title, subtitle, key in section_defs:
            card(num, title, subtitle, state["parts"].get(key) or "Not available",
                 card_color, emphasis=True)
        y += 7
        if lab == "object":
            try:
                distance = float(result.get("distance"))
                delta = float(result.get("displacement_magnitude"))
                if distance >= 0 and delta > distance + max(.1, .002 * distance):
                    card("!", "MEASUREMENT WARNING", "Check tracking accuracy",
                         "Recorded displacement exceeds the tracked path. Exact displacement "
                         "cannot exceed total distance traveled; treat this as measurement "
                         "inconsistency, not verified straight-line motion.",
                         ("#473a2c" if dark else "#fff1d7"), True)
            except (TypeError, ValueError):
                pass
        y += 7
        # One textbook principle chosen deterministically from the lab and measured trend.
        # No extra model request, and no inferred numeric forces or accelerations.
        principle = choose_physics_principle(lab, result, report)
        center("Physics Principle", section_font, foreground, 9)
        card("", principle["title"], principle["formula"],
             principle["explanation"] + "\n\n" + principle["limitation"],
             card_secondary)
        y += 7
        center("Motion Analysis", section_font, foreground, 3)
        center("Estimated phases calculated from saved tracking samples", caption_font, secondary, 13)
        card("", "TRACKING SUMMARY", "", report.get("summary", "No motion report."), card_secondary)
        for event in report.get("segments", []):
            card("", str(event.get("label", "Motion interval")) + "  |  " +
                 str(event.get("time", "")), "", event.get("description", ""), card_secondary)
        note = report.get("confidence_note", "")
        if note:
            y += put(left + 10, y + 3, note, caption_font, secondary, content_width - 20) + 24
        else:
            y += 18
        center("Formula Explorer", section_font, foreground, 14)
        if not formulas:
            card("", "MEASUREMENTS", "", "Insufficient data for formulas.", card_secondary)
        for formula in formulas:
            card("", str(formula.get("title", "FORMULA")),
                 str(formula.get("formula", "")),
                 str(formula.get("substitution", "")) + "\n\n" +
                 str(formula.get("explanation", "")), card_secondary)
        y += put(left + 10, y + 6,
                 "Values come from saved camera samples. Peaks can reflect tracking noise; "
                 "pixel units require calibration for real-world measurements.",
                 caption_font, secondary, content_width - 20) + 30
        canvas.configure(scrollregion=(0, 0, width, max(y, canvas.winfo_height())))
        canvas.yview_moveto(view_fraction if preserve else 0)

    def schedule_redraw(event=None):
        if redraw_id["value"] is not None:
            try:
                canvas.after_cancel(redraw_id["value"])
            except tk.TclError:
                pass
        redraw_id["value"] = canvas.after(90, lambda: (redraw_id.update(value=None), draw()))

    canvas.bind("<Configure>", schedule_redraw)
    canvas.bind("<MouseWheel>", lambda event: canvas.yview_scroll(
        -max(-6, min(6, round(event.delta / 120))) * 2, "units"))
    canvas.bind("<Button-4>", lambda event: canvas.yview_scroll(-2, "units"))
    canvas.bind("<Button-5>", lambda event: canvas.yview_scroll(2, "units"))
    canvas.after(110, lambda: draw(preserve=False))

    # Background thread does no Tk work. Tk polls a queue from its own event loop.
    results_queue = queue.Queue(maxsize=1)

    def worker():
        try:
            results_queue.put(explain_story_with_ai(lab, result))
        except Exception:
            results_queue.put(("offline", "AI explanation unavailable. Please retry later."))

    def check_ai():
        try:
            source, message = results_queue.get_nowait()
        except queue.Empty:
            if canvas.winfo_exists():
                canvas.after(150, check_ai)
            return
        if not canvas.winfo_exists():
            return
        sections = parse_story_sections(message)
        for key in ("HOW IT MOVED", "WHY IT CHANGED", "PHYSICS BEHIND IT", "WHAT WE LEARNED"):
            parts[key] = sections.get(key) or (message if key == "HOW IT MOVED" else "Not available")
        state["source"] = source
        if status_text.winfo_exists():
            status_text.configure(text=("AI Motion Insight · OpenAI" if source == "ai"
                                       else "Local physics explanation"))
        draw(preserve=True)

    threading.Thread(target=worker, daemon=True).start()
    canvas.after(150, check_ai)


def show_home():
    """Clean main menu: three active modes, legacy modes one click away."""
    global _eureka_status
    clear_screen()

    page = ctk.CTkFrame(app, fg_color="transparent")
    page.pack(fill="both", expand=True, padx=34, pady=20)
    ctk.CTkLabel(page, text="PhysiLearn",
                 font=ctk.CTkFont(size=42, weight="bold")).pack(pady=(10, 3))
    ctk.CTkLabel(page, text="Turn everyday objects into physics experiments",
                 font=ctk.CTkFont(size=16),
                 text_color=("gray40", "gray75")).pack(pady=(0, 8))

    _eureka_status = ctk.CTkLabel(page, text="Choose an experiment to begin",
                                  font=ctk.CTkFont(size=12),
                                  text_color=("gray40", "gray75"), wraplength=900)
    _eureka_status.pack(pady=(0, 20))

    choices = ctk.CTkFrame(page, fg_color="transparent")
    choices.pack(fill="x", padx=22)
    choices.grid_columnconfigure((0, 1), weight=1, uniform="labs")

    def main_card(column, icon, name, description, button, command):
        card = ctk.CTkFrame(choices, corner_radius=17)
        card.grid(row=0, column=column, sticky="nsew", padx=10, pady=6)
        ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=27)).pack(pady=(18, 5))
        ctk.CTkLabel(card, text=name,
                     font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(0, 4))
        ctk.CTkLabel(card, text=description,
                     font=ctk.CTkFont(size=13), justify="center",
                     wraplength=330, text_color=("gray40", "gray75")).pack(padx=15, pady=(0, 14))
        ctk.CTkButton(card, text=button, command=command,
                      height=39, width=198, corner_radius=11,
                      font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(0, 19))

    main_card(0, "🚗", "Object Physics Lab",
              "Track a toy car, ball or box. Measure distance, speed and motion.",
              "Start Object Lab  →", show_object_picker)
    main_card(1, "📐", "Ramp Physics Lab",
              "Explore how a moving object behaves on a small incline.",
              "Start Ramp Lab  →", show_ramp_launcher)

    compare = ctk.CTkFrame(page, corner_radius=17)
    compare.pack(fill="x", padx=32, pady=(15, 12))
    compare.grid_columnconfigure(0, weight=1)
    left = ctk.CTkFrame(compare, fg_color="transparent")
    left.grid(row=0, column=0, sticky="w", padx=24, pady=16)
    ctk.CTkLabel(left, text="📊  Compare Experiments",
                 font=ctk.CTkFont(size=19, weight="bold"), anchor="w").pack(anchor="w")
    ctk.CTkLabel(left, text="See how two saved recordings differ.",
                 font=ctk.CTkFont(size=13),
                 text_color=("gray40", "gray75"), anchor="w").pack(anchor="w", pady=(4, 0))
    ctk.CTkButton(compare, text="Compare Runs  →", width=177, height=39,
                  command=lambda: __import__("physilearn_compare_gui").open_comparison_window(app)
                  ).grid(row=0, column=1, padx=24, pady=15)

    ctk.CTkButton(page, text="Classic Labs  ·  More modes  →",
                  command=show_classic_labs, width=245, height=34,
                  fg_color="transparent", border_width=1,
                  border_color=("gray65", "gray45"),
                  text_color=("gray25", "gray85"),
                  hover_color=("gray86", "gray23")).pack(pady=(5, 0))


def show_classic_labs():
    """Keep all legacy features accessible without crowding the front page."""
    global _eureka_status
    clear_screen()
    page = ctk.CTkFrame(app, fg_color="transparent")
    page.pack(fill="both", expand=True, padx=38, pady=23)
    ctk.CTkButton(page, text="← Back to Home", width=175, height=36,
                  command=show_home).pack(anchor="w", pady=(0, 22))
    ctk.CTkLabel(page, text="Classic Labs",
                 font=ctk.CTkFont(size=34, weight="bold")).pack(pady=(5, 4))
    ctk.CTkLabel(page, text="Earlier PhysiLearn learning modes, kept for exploration",
                 font=ctk.CTkFont(size=14),
                 text_color=("gray40", "gray75")).pack(pady=(0, 20))
    classics = ctk.CTkFrame(page, fg_color="transparent")
    classics.pack(fill="x", padx=45)
    classics.grid_columnconfigure((0, 1), weight=1, uniform="classic")

    for i, (icon, title, desc, button, action) in enumerate((
        ("🎾", "Tennis Ball Physics", "Original tennis-ball experiment and questions.",
         "Open Ball Lab", show_ball_challenge),
        ("✋", "Constant Velocity Challenge", "Practice maintaining steady hand motion.",
         "Open Hand Challenge", show_challenge),
    )):
        card = ctk.CTkFrame(classics, corner_radius=15)
        card.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=28)).pack(pady=(20, 7))
        ctk.CTkLabel(card, text=title,
                     font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(0, 4))
        ctk.CTkLabel(card, text=desc, font=ctk.CTkFont(size=12),
                     text_color=("gray40", "gray75"), wraplength=290).pack(padx=12)
        ctk.CTkButton(card, text=button, command=action,
                      width=210, height=39).pack(pady=(16, 20))

    ctk.CTkButton(page, text="Open original PhysiLearn menu",
                  command=show_legacy_home, width=270, height=39,
                  fg_color=("gray70", "gray32"),
                  hover_color=("gray62", "gray39")).pack(pady=(26, 12))
    _eureka_status = ctk.CTkLabel(page, text="",
                                  text_color=("gray40", "gray75"))
    _eureka_status.pack()



show_home()
app.mainloop()