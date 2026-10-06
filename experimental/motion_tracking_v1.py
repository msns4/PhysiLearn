import cv2
import mediapipe as mp
import time

# MediaPipe Tasks
BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

options = HandLandmarkerOptions(
    base_options=BaseOptions(model_asset_path="hand_landmarker.task"),
    running_mode=VisionRunningMode.IMAGE,
    num_hands=1
)

landmarker = HandLandmarker.create_from_options(options)

cap = cv2.VideoCapture(0)

# Previous measurements
previous_x = None
previous_time = None
previous_velocity = None

# Smoothed values
velocity_x = 0.0
acceleration_x = 0.0

while True:
    ret, frame = cap.read()

    if not ret:
        break

    frame = cv2.flip(frame, 1)

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb_frame
    )

    result = landmarker.detect(mp_image)

    if result.hand_landmarks:

        hand = result.hand_landmarks[0]
        height, width, _ = frame.shape

        # Draw all landmarks
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

        # Landmark 0 = wrist
        wrist = hand[0]

        wrist_x = int(wrist.x * width)
        wrist_y = int(wrist.y * height)

        # Highlight wrist
        cv2.circle(
            frame,
            (wrist_x, wrist_y),
            10,
            (0, 0, 255),
            -1
        )

        current_time = time.perf_counter()

        if previous_x is not None and previous_time is not None:

            delta_x = wrist.x - previous_x
            delta_t = current_time - previous_time

            if delta_t > 0:

                # ----- VELOCITY -----
                raw_velocity = delta_x / delta_t

                velocity_x = (
                    0.8 * velocity_x
                    + 0.2 * raw_velocity
                )

                # ----- ACCELERATION -----
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

        # Determine direction
        if velocity_x > 0.05:
            direction = "RIGHT"

        elif velocity_x < -0.05:
            direction = "LEFT"

        else:
            direction = "STOPPED"

        # Position
        cv2.putText(
            frame,
            f"Position X: {wrist.x:.3f}",
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2
        )

        # Velocity
        cv2.putText(
            frame,
            f"Velocity X: {velocity_x:+.3f} units/s",
            (30, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2
        )

        # Acceleration
        cv2.putText(
            frame,
            f"Acceleration X: {acceleration_x:+.3f} units/s^2",
            (30, 130),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2
        )

        # Direction
        cv2.putText(
            frame,
            f"Motion: {direction}",
            (30, 170),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2
        )

    cv2.imshow("PhysiLearn - Motion Physics", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
landmarker.close()
cv2.destroyAllWindows()