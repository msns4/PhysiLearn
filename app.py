import customtkinter as ctk

import subprocess

import sys

import os

import json

import threading



from ai_tutor import generate_tutor_feedback





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


# =========================================================

# HOME SCREEN

# =========================================================



def show_home():



    clear_screen()



    main_frame = ctk.CTkFrame(

        app,

        corner_radius=0

    )



    main_frame.pack(

        fill="both",

        expand=True

    )





    # -----------------------------------------------------

    # LOGO

    # -----------------------------------------------------



    logo = ctk.CTkLabel(

        main_frame,

        text="PhysiLearn",

        font=ctk.CTkFont(

            size=42,

            weight="bold"

        )

    )



    logo.pack(

        pady=(65, 5)

    )





    subtitle = ctk.CTkLabel(

        main_frame,

        text=(

            "Learn physics through your own movement."

        ),

        font=ctk.CTkFont(

            size=20

        )

    )



    subtitle.pack(

        pady=(0, 40)

    )





    # -----------------------------------------------------

    # MAIN CARD

    # -----------------------------------------------------



    physics_card = ctk.CTkFrame(

        main_frame,

        width=620,

        height=320,

        corner_radius=25

    )



    physics_card.pack(

        pady=10

    )



    physics_card.pack_propagate(

        False

    )





    physics_title = ctk.CTkLabel(

        physics_card,

        text="Interactive Motion Lab",

        font=ctk.CTkFont(

            size=30,

            weight="bold"

        )

    )



    physics_title.pack(

        pady=(40, 10)

    )





    physics_description = ctk.CTkLabel(

        physics_card,

        text=(

            "Turn your webcam into a motion laboratory.\n"

            "Move your hand, run real experiments, and understand\n"

            "position, velocity, and acceleration."

        ),

        font=ctk.CTkFont(

            size=17

        ),

        justify="center"

    )



    physics_description.pack(

        pady=15

    )





    start_button = ctk.CTkButton(

        physics_card,

        text="Start Learning",

        command=show_challenge,

        width=260,

        height=55,

        corner_radius=15,

        font=ctk.CTkFont(

            size=18,

            weight="bold"

        )

    )



    start_button.pack(

        pady=25

    )





    footer = ctk.CTkLabel(

        main_frame,

        text=(

            "Computer Vision  •  Physics  •  "

            "AI-Powered Learning"

        ),

        font=ctk.CTkFont(

            size=14

        )

    )



    footer.pack(

        pady=25

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



show_home()



app.mainloop()