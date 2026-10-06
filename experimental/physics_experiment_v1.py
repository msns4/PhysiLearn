import cv2
import mediapipe as mp
import time
import matplotlib.pyplot as plt

# ---------------- MediaPipe setup ----------------

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

landmarker = HandLandmarker.create_from_options(options)
cap = cv2.VideoCapture(0)

# ---------------- Physics variables ----------------

previous_x = None
previous_time = None
previous_velocity = None

velocity_x = 0.0
acceleration_x = 0.0

# Experiment data
times = []
positions = []
velocities = []
accelerations = []

recording = False
experiment_start = None


# ---------------- Main loop ----------------

while True:

    ret, frame = cap.read()

    if not ret:
        break

    frame = cv2.flip(frame, 1)

    rgb_frame = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb_frame
    )

    result = landmarker.detect(mp_image)

    if result.hand_landmarks:

        hand = result.hand_landmarks[0]

        height, width, _ = frame.shape

        # Draw landmarks
        for landmark in hand:

            x = int(landmark.x * width)
            y = int(landmark.y * height)

            cv2.circle(
                frame,
                (x, y),
                4,
                (0, 255, 0),
                -1
            )

        # Wrist = landmark 0
        wrist = hand[0]

        wrist_x = int(wrist.x * width)
        wrist_y = int(wrist.y * height)

        cv2.circle(
            frame,
            (wrist_x, wrist_y),
            10,
            (0, 0, 255),
            -1
        )

        current_time = time.perf_counter()

        # ---------------- Velocity ----------------

        if previous_x is not None and previous_time is not None:

            delta_x = wrist.x - previous_x
            delta_t = current_time - previous_time

            if delta_t > 0:

                raw_velocity = delta_x / delta_t

                velocity_x = (
                    0.8 * velocity_x
                    + 0.2 * raw_velocity
                )

                # ---------------- Acceleration ----------------

                if previous_velocity is not None:

                    raw_acceleration = (
                        velocity_x - previous_velocity
                    ) / delta_t

                    acceleration_x = (
                        0.85 * acceleration_x
                        + 0.15 * raw_acceleration
                    )

                previous_velocity = velocity_x

        previous_x = wrist.x
        previous_time = current_time

        # ---------------- Record experiment ----------------

        if recording:

            elapsed_time = (
                current_time - experiment_start
            )

            times.append(elapsed_time)
            positions.append(wrist.x)
            velocities.append(velocity_x)
            accelerations.append(acceleration_x)

        # ---------------- Direction ----------------

        if velocity_x > 0.05:
            direction = "RIGHT"

        elif velocity_x < -0.05:
            direction = "LEFT"

        else:
            direction = "STOPPED"

        # ---------------- Display physics ----------------

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

    # ---------------- Recording status ----------------

    if recording:

        cv2.putText(
            frame,
            "RECORDING",
            (30, 205),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (0, 0, 255),
            3
        )

    else:

        cv2.putText(
            frame,
            "Press S to start experiment",
            (30, 205),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

    cv2.putText(
        frame,
        "S = Start   E = End   Q = Quit",
        (30, 245),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2
    )

    cv2.imshow(
        "PhysiLearn - Physics Experiment",
        frame
    )

    key = cv2.waitKey(1) & 0xFF

    # ---------------- Start experiment ----------------

    if key == ord("s"):

        times.clear()
        positions.clear()
        velocities.clear()
        accelerations.clear()

        experiment_start = time.perf_counter()

        recording = True

        print("Experiment started.")

    # ---------------- End experiment ----------------

    elif key == ord("e"):

        if recording:

            recording = False

            print("Experiment finished.")
            print(f"Recorded {len(times)} data points.")

            break

    # ---------------- Quit ----------------

    elif key == ord("q"):
        break


# ---------------- Cleanup ----------------

cap.release()
landmarker.close()
cv2.destroyAllWindows()


# ---------------- Graphs ----------------

if len(times) > 5:

    # Position graph
    plt.figure()

    plt.plot(
        times,
        positions
    )

    plt.title("Position vs Time")
    plt.xlabel("Time (s)")
    plt.ylabel("Position (relative units)")
    plt.grid(True)

    # Velocity graph
    plt.figure()

    plt.plot(
        times,
        velocities
    )

    plt.title("Velocity vs Time")
    plt.xlabel("Time (s)")
    plt.ylabel("Velocity (relative units/s)")
    plt.axhline(0)
    plt.grid(True)

    # Acceleration graph
    plt.figure()

    plt.plot(
        times,
        accelerations
    )

    plt.title("Acceleration vs Time")
    plt.xlabel("Time (s)")
    plt.ylabel("Acceleration (relative units/s^2)")
    plt.axhline(0)
    plt.grid(True)

    plt.show()