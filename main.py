import cv2
import mediapipe as mp
import time
import matplotlib.pyplot as plt
import statistics
import json


# =========================================================
# SETTINGS
# =========================================================

COUNTDOWN_SECONDS = 3
RECORDING_SECONDS = 4


# =========================================================
# MEDIAPIPE SETUP
# =========================================================

BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

options = HandLandmarkerOptions(
    base_options=BaseOptions(
        model_asset_path="hand_landmarker.task"
    ),
    running_mode=VisionRunningMode.IMAGE,
    num_hands=1
)

landmarker = HandLandmarker.create_from_options(
    options
)

cap = cv2.VideoCapture(0)


# =========================================================
# PHYSICS VARIABLES
# =========================================================

previous_x = None
previous_time = None
previous_velocity = None

velocity_x = 0.0
acceleration_x = 0.0


# =========================================================
# EXPERIMENT DATA
# =========================================================

times = []
positions = []
velocities = []
accelerations = []

recording = False
experiment_start = None

countdown_start = time.perf_counter()

experiment_finished = False


# =========================================================
# SAVE RESULT
# =========================================================

def save_result(result_data):

    with open(
        "experiment_result.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            result_data,
            file,
            indent=4
        )

    print("Experiment result saved.")


# =========================================================
# EXPERIMENT ANALYSIS
# =========================================================

def analyze_experiment(
    velocities,
    accelerations
):

    total_points = len(
        velocities
    )

    # -----------------------------------------------------
    # CHECK DATA AMOUNT
    # -----------------------------------------------------

    if total_points < 30:

        print(
            "\nNot enough data to analyze."
        )

        result_data = {
            "challenge": "Constant Velocity",
            "status": "NOT_ENOUGH_DATA",
            "passed": False,
            "feedback": [
                "Not enough motion data was recorded."
            ],
            "concept": (
                "Constant velocity requires both "
                "constant speed and constant direction."
            ),
            "how_to_improve": (
                "Keep your hand visible and move "
                "smoothly during the experiment."
            )
        }

        save_result(
            result_data
        )

        return result_data


    # -----------------------------------------------------
    # REMOVE START / END SECTIONS
    # -----------------------------------------------------

    # Starting and stopping naturally create acceleration.
    # We evaluate mainly the middle part of the movement.

    trim = max(
        5,
        int(
            total_points * 0.10
        )
    )

    clean_velocities = velocities[
        trim:-trim
    ]

    clean_accelerations = accelerations[
        trim:-trim
    ]


    if len(
        clean_velocities
    ) < 10:

        print(
            "\nNot enough clean data to analyze."
        )

        result_data = {
            "challenge": "Constant Velocity",
            "status": "NOT_ENOUGH_DATA",
            "passed": False,
            "feedback": [
                "Not enough usable motion data was recorded."
            ],
            "concept": (
                "Constant velocity requires both "
                "constant speed and constant direction."
            ),
            "how_to_improve": (
                "Keep your hand visible and move "
                "through the full recording period."
            )
        }

        save_result(
            result_data
        )

        return result_data


    # =====================================================
    # BASIC MEASUREMENTS
    # =====================================================

    avg_velocity = statistics.mean(
        clean_velocities
    )

    velocity_stdev = statistics.stdev(
        clean_velocities
    )

    avg_abs_acceleration = statistics.mean(
        abs(a)
        for a in clean_accelerations
    )

    max_velocity = max(
        clean_velocities
    )

    min_velocity = min(
        clean_velocities
    )


    # =====================================================
    # DIRECTION CONSISTENCY
    # =====================================================

    # Ignore tiny velocities caused by tracking noise
    # or very small hand movement.

    movement_threshold = 0.05

    moving_velocities = [
        velocity
        for velocity in clean_velocities
        if abs(
            velocity
        ) > movement_threshold
    ]


    if len(
        moving_velocities
    ) > 0:

        right_frames = sum(
            1
            for velocity in moving_velocities
            if velocity > 0
        )

        direction_consistency = (
            right_frames
            / len(
                moving_velocities
            )
        )

    else:

        direction_consistency = 0.0


    direction_consistency_percent = (
        direction_consistency * 100
    )


    # =====================================================
    # EVALUATION
    # =====================================================

    steady_velocity = (
        velocity_stdev < 0.25
    )

    low_acceleration = (
        avg_abs_acceleration < 0.45
    )

    consistent_direction = (
        direction_consistency >= 0.85
    )

    passed = (
        steady_velocity
        and low_acceleration
        and consistent_direction
    )


    # =====================================================
    # FEEDBACK
    # =====================================================

    feedback = []


    if not consistent_direction:

        feedback.append(
            "Your movement was not consistently "
            "from left to right."
        )


    if not steady_velocity:

        feedback.append(
            "Your velocity changed too much."
        )


    if not low_acceleration:

        feedback.append(
            "Your acceleration was high, which "
            "means your velocity was changing."
        )


    if passed:

        feedback.append(
            "You moved mostly in one direction."
        )

        feedback.append(
            "Your velocity stayed relatively stable."
        )

        feedback.append(
            "Your acceleration remained small."
        )


    # =====================================================
    # RESULT DATA
    # =====================================================

    result_data = {

        "challenge": "Constant Velocity",

        "status": (
            "PASS"
            if passed
            else "TRY_AGAIN"
        ),

        "passed": passed,

        "average_velocity": round(
            avg_velocity,
            3
        ),

        "velocity_variation": round(
            velocity_stdev,
            3
        ),

        "average_acceleration": round(
            avg_abs_acceleration,
            3
        ),

        "maximum_velocity": round(
            max_velocity,
            3
        ),

        "minimum_velocity": round(
            min_velocity,
            3
        ),

        "direction_consistency": round(
            direction_consistency_percent,
            1
        ),

        "feedback": feedback,

        "concept": (
            "Constant velocity requires both "
            "constant speed and constant direction."
        ),

        "how_to_improve": (
            "Move your hand smoothly from left "
            "to right at a steady speed without "
            "reversing direction."
        )
    }


    # =====================================================
    # TERMINAL OUTPUT
    # =====================================================

    print(
        "\n----------------------------------"
    )

    print(
        "PHYSILEARN EXPERIMENT ANALYSIS"
    )

    print(
        "----------------------------------"
    )

    print(
        f"Average velocity:       "
        f"{avg_velocity:+.3f}"
    )

    print(
        f"Velocity variation:     "
        f"{velocity_stdev:.3f}"
    )

    print(
        f"Average acceleration:   "
        f"{avg_abs_acceleration:.3f}"
    )

    print(
        f"Direction consistency:  "
        f"{direction_consistency_percent:.1f}%"
    )

    print(
        f"Maximum velocity:       "
        f"{max_velocity:+.3f}"
    )

    print(
        f"Minimum velocity:       "
        f"{min_velocity:+.3f}"
    )

    print(
        "----------------------------------"
    )


    if passed:

        print(
            "\nRESULT: PASS"
        )

        print(
            "\nGreat job! Your hand moved with "
            "approximately constant velocity."
        )

        print(
            "\nWHY?"
        )

        for message in feedback:

            print(
                f"- {message}"
            )

    else:

        print(
            "\nRESULT: TRY AGAIN"
        )

        print(
            "\nFEEDBACK:"
        )

        for message in feedback:

            print(
                f"- {message}"
            )

        print(
            "\nHOW TO IMPROVE:"
            "\nMove your hand smoothly from left "
            "to right at a steady speed without "
            "reversing direction."
        )


    print(
        "\nPHYSICS CONCEPT:"
        "\nConstant velocity requires both constant "
        "speed and constant direction."
    )

    print(
        "\n----------------------------------\n"
    )


    save_result(
        result_data
    )

    return result_data


# =========================================================
# RESET PHYSICS TRACKING
# =========================================================

def reset_tracking():

    global previous_x
    global previous_time
    global previous_velocity
    global velocity_x
    global acceleration_x

    previous_x = None
    previous_time = None
    previous_velocity = None

    velocity_x = 0.0
    acceleration_x = 0.0


# =========================================================
# DRAW CENTERED TEXT
# =========================================================

def draw_centered_text(
    frame,
    text,
    y,
    scale,
    color,
    thickness
):

    font = cv2.FONT_HERSHEY_SIMPLEX

    text_size = cv2.getTextSize(
        text,
        font,
        scale,
        thickness
    )[0]

    x = int(
        (
            frame.shape[1]
            - text_size[0]
        ) / 2
    )

    cv2.putText(
        frame,
        text,
        (x, y),
        font,
        scale,
        color,
        thickness
    )


# =========================================================
# MAIN LOOP
# =========================================================

while True:

    ret, frame = cap.read()

    if not ret:
        break


    # Mirror webcam
    frame = cv2.flip(
        frame,
        1
    )


    current_clock = time.perf_counter()


    # =====================================================
    # COUNTDOWN / AUTO START
    # =====================================================

    if not recording:

        countdown_elapsed = (
            current_clock
            - countdown_start
        )

        countdown_remaining = (
            COUNTDOWN_SECONDS
            - countdown_elapsed
        )


        if countdown_remaining > 0:

            countdown_number = int(
                countdown_remaining
            ) + 1

            draw_centered_text(
                frame,
                "GET READY",
                80,
                1.0,
                (255, 255, 255),
                2
            )

            draw_centered_text(
                frame,
                str(
                    countdown_number
                ),
                180,
                3.0,
                (0, 255, 255),
                5
            )

            draw_centered_text(
                frame,
                "Place your hand in view",
                230,
                0.7,
                (255, 255, 255),
                2
            )

        else:

            times.clear()
            positions.clear()
            velocities.clear()
            accelerations.clear()

            reset_tracking()

            experiment_start = (
                time.perf_counter()
            )

            recording = True

            print(
                "Experiment started automatically."
            )


    # -----------------------------------------------------
    # MEDIAPIPE IMAGE
    # -----------------------------------------------------

    rgb_frame = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb_frame
    )

    result = landmarker.detect(
        mp_image
    )


    # =====================================================
    # HAND DETECTED
    # =====================================================

    if result.hand_landmarks:

        hand = result.hand_landmarks[0]

        height, width, _ = frame.shape


        # -------------------------------------------------
        # DRAW LANDMARKS
        # -------------------------------------------------

        for landmark in hand:

            x = int(
                landmark.x * width
            )

            y = int(
                landmark.y * height
            )

            cv2.circle(
                frame,
                (x, y),
                4,
                (0, 255, 0),
                -1
            )


        # -------------------------------------------------
        # WRIST
        # -------------------------------------------------

        wrist = hand[0]

        wrist_x = int(
            wrist.x * width
        )

        wrist_y = int(
            wrist.y * height
        )

        cv2.circle(
            frame,
            (wrist_x, wrist_y),
            10,
            (0, 0, 255),
            -1
        )


        current_time = (
            time.perf_counter()
        )


        # =================================================
        # VELOCITY
        # =================================================

        if (
            previous_x is not None
            and previous_time is not None
        ):

            delta_x = (
                wrist.x
                - previous_x
            )

            delta_t = (
                current_time
                - previous_time
            )


            if delta_t > 0:

                raw_velocity = (
                    delta_x
                    / delta_t
                )

                # Smooth velocity
                velocity_x = (
                    0.8 * velocity_x
                    + 0.2 * raw_velocity
                )


                # =========================================
                # ACCELERATION
                # =========================================

                if previous_velocity is not None:

                    raw_acceleration = (
                        velocity_x
                        - previous_velocity
                    ) / delta_t

                    # Smooth acceleration
                    acceleration_x = (
                        0.85 * acceleration_x
                        + 0.15 * raw_acceleration
                    )


                previous_velocity = (
                    velocity_x
                )


        previous_x = wrist.x
        previous_time = current_time


        # =================================================
        # RECORD DATA
        # =================================================

        if recording:

            elapsed_time = (
                current_time
                - experiment_start
            )

            times.append(
                elapsed_time
            )

            positions.append(
                wrist.x
            )

            velocities.append(
                velocity_x
            )

            accelerations.append(
                acceleration_x
            )


        # =================================================
        # CURRENT DIRECTION
        # =================================================

        if velocity_x > 0.05:

            direction = "RIGHT"

        elif velocity_x < -0.05:

            direction = "LEFT"

        else:

            direction = "STOPPED"


        # =================================================
        # DISPLAY VALUES
        # =================================================

        cv2.putText(
            frame,
            f"Position: {wrist.x:.3f}",
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"Velocity: {velocity_x:+.3f}",
            (30, 85),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"Acceleration: {acceleration_x:+.3f}",
            (30, 120),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"Motion: {direction}",
            (30, 155),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (255, 255, 255),
            2
        )


    # =====================================================
    # RECORDING DISPLAY + AUTO STOP
    # =====================================================

    if recording:

        recording_elapsed = (
            current_clock
            - experiment_start
        )

        recording_remaining = max(
            0.0,
            RECORDING_SECONDS
            - recording_elapsed
        )


        cv2.putText(
            frame,
            "RECORDING",
            (30, 205),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (0, 0, 255),
            3
        )


        cv2.putText(
            frame,
            (
                f"Time left: "
                f"{recording_remaining:.1f}s"
            ),
            (30, 245),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )


        # -------------------------------------------------
        # AUTOMATIC END
        # -------------------------------------------------

        if (
            recording_elapsed
            >= RECORDING_SECONDS
        ):

            recording = False
            experiment_finished = True

            print(
                "Experiment finished automatically."
            )

            print(
                f"Recorded {len(times)} "
                f"data points."
            )

            analyze_experiment(
                velocities,
                accelerations
            )


    # =====================================================
    # SHOW WINDOW
    # =====================================================

    cv2.imshow(
        "PhysiLearn - Physics Experiment",
        frame
    )


    # Keyboard is now only an emergency quit.
    # The experiment itself does not depend on keyboard input.
    key = cv2.waitKey(1) & 0xFF

    if key == 27:
        break


    # Give OpenCV one final rendered frame,
    # then leave after automatic analysis.
    if experiment_finished:

        cv2.waitKey(500)

        break


# =========================================================
# CLEANUP
# =========================================================

cap.release()

landmarker.close()

cv2.destroyAllWindows()


# =========================================================
# GRAPHS
# =========================================================

if len(times) > 5:

    # ---------------- POSITION ----------------

    plt.figure()

    plt.plot(
        times,
        positions
    )

    plt.title(
        "Position vs Time"
    )

    plt.xlabel(
        "Time (s)"
    )

    plt.ylabel(
        "Position (relative units)"
    )

    plt.grid(True)


    # ---------------- VELOCITY ----------------

    plt.figure()

    plt.plot(
        times,
        velocities
    )

    plt.title(
        "Velocity vs Time"
    )

    plt.xlabel(
        "Time (s)"
    )

    plt.ylabel(
        "Velocity (relative units/s)"
    )

    plt.axhline(0)

    plt.grid(True)


    # ---------------- ACCELERATION ----------------

    plt.figure()

    plt.plot(
        times,
        accelerations
    )

    plt.title(
        "Acceleration vs Time"
    )

    plt.xlabel(
        "Time (s)"
    )

    plt.ylabel(
        "Acceleration (relative units/s^2)"
    )

    plt.axhline(0)

    plt.grid(True)

    plt.show()