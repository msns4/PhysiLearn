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
app.geometry("1000x650")
app.minsize(900, 600)


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

    try:

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
        # FALLBACK
        # -------------------------------------------------

        # The app should still work if the API is
        # unavailable during a demo.

        feedback = result_data.get(
            "feedback",
            []
        )

        concept = result_data.get(
            "concept",
            ""
        )

        how_to_improve = result_data.get(
            "how_to_improve",
            ""
        )


        fallback_parts = []


        if feedback:

            fallback_parts.append(
                " ".join(
                    feedback
                )
            )


        if concept:

            fallback_parts.append(
                concept
            )


        if (
            not result_data.get(
                "passed",
                False
            )
            and how_to_improve
        ):

            fallback_parts.append(
                how_to_improve
            )


        if fallback_parts:

            result_data[
                "ai_feedback"
            ] = " ".join(
                fallback_parts
            )

        else:

            result_data[
                "ai_feedback"
            ] = (
                "Your motion was analyzed successfully. "
                "Review the measurements above and try "
                "the experiment again to compare your results."
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
        (
            "Your motion was analyzed successfully."
        )
    )


    # -----------------------------------------------------
    # TITLE
    # -----------------------------------------------------

    title = ctk.CTkLabel(
        result_frame,
        text="Experiment Complete",
        font=ctk.CTkFont(
            size=36,
            weight="bold"
        )
    )

    title.pack(
        pady=(30, 5)
    )


    # -----------------------------------------------------
    # STATUS
    # -----------------------------------------------------

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
            size=28,
            weight="bold"
        )
    )

    status_label.pack(
        pady=(0, 12)
    )


    # -----------------------------------------------------
    # MAIN CARD
    # -----------------------------------------------------

    card = ctk.CTkFrame(
        result_frame,
        width=760,
        height=405,
        corner_radius=24
    )

    card.pack(
        pady=5
    )

    card.pack_propagate(
        False
    )


    # -----------------------------------------------------
    # YOUR MOTION
    # -----------------------------------------------------

    motion_title = ctk.CTkLabel(
        card,
        text="YOUR MOTION",
        font=ctk.CTkFont(
            size=18,
            weight="bold"
        )
    )

    motion_title.pack(
        pady=(27, 8)
    )


    if (
        direction_consistency == "N/A"
        or velocity_variation == "N/A"
        or average_acceleration == "N/A"
    ):

        measurements_text = (
            "Not enough motion data was recorded."
        )

    else:

        measurements_text = (
            f"Direction consistency: "
            f"{direction_consistency}%\n"
            f"Velocity variation: "
            f"{velocity_variation}\n"
            f"Average acceleration: "
            f"{average_acceleration}"
        )


    measurements = ctk.CTkLabel(
        card,
        text=measurements_text,
        font=ctk.CTkFont(
            size=17
        ),
        justify="center"
    )

    measurements.pack(
        pady=(0, 22)
    )


    # -----------------------------------------------------
    # AI PHYSICS TUTOR
    # -----------------------------------------------------

    ai_title = ctk.CTkLabel(
        card,
        text="AI PHYSICS TUTOR",
        font=ctk.CTkFont(
            size=18,
            weight="bold"
        )
    )

    ai_title.pack(
        pady=(0, 10)
    )


    ai_label = ctk.CTkLabel(
        card,
        text=ai_feedback,
        font=ctk.CTkFont(
            size=16
        ),
        justify="left",
        wraplength=650
    )

    ai_label.pack(
        padx=45,
        pady=(0, 20)
    )


    ai_note = ctk.CTkLabel(
        card,
        text=(
            "Personalized from your motion measurements"
        ),
        font=ctk.CTkFont(
            size=12
        )
    )

    ai_note.pack(
        pady=(0, 15)
    )


    # -----------------------------------------------------
    # BUTTONS
    # -----------------------------------------------------

    button_frame = ctk.CTkFrame(
        result_frame,
        fg_color="transparent"
    )

    button_frame.pack(
        pady=18
    )


    retry_button = ctk.CTkButton(
        button_frame,
        text="Try Again",
        command=show_challenge,
        width=190,
        height=48,
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
        height=48,
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