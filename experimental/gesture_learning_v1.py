import cv2
import mediapipe as mp
import random
import time
import math
from collections import deque

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

# ---------------- Quiz settings ----------------

LETTERS = ["A", "B", "I", "L", "Y"]

target_letter = random.choice(LETTERS)

score = 0

correct_start_time = None
HOLD_TIME = 0.8

message = ""
message_until = 0

# Keep recent predictions for stability
prediction_history = deque(maxlen=5)


# ---------------- Helper functions ----------------

def distance(p1, p2):
    return math.sqrt(
        (p1.x - p2.x) ** 2 +
        (p1.y - p2.y) ** 2
    )


def finger_is_up(hand, tip, pip):
    """
    Index, middle, ring and pinky:
    fingertip should be above the PIP joint.
    """
    return hand[tip].y < hand[pip].y


def thumb_is_extended(hand):
    """
    Detect whether the thumb is extended away from the palm.

    Landmark:
    0  = wrist
    2  = thumb MCP
    4  = thumb tip
    5  = index MCP
    17 = pinky MCP
    """

    thumb_tip = hand[4]
    thumb_mcp = hand[2]
    index_mcp = hand[5]
    pinky_mcp = hand[17]

    # Approximate palm width
    palm_width = distance(index_mcp, pinky_mcp)

    # Distance from thumb tip to index base
    thumb_to_index = distance(thumb_tip, index_mcp)

    # Distance from thumb tip to its own base
    thumb_length = distance(thumb_tip, thumb_mcp)

    # Thumb must clearly extend away from the palm
    return (
        thumb_to_index > palm_width * 0.75
        and thumb_length > palm_width * 0.45
    )


# ---------------- ASL detection ----------------

def detect_asl_letter(hand):

    thumb = thumb_is_extended(hand)

    index = finger_is_up(hand, 8, 6)
    middle = finger_is_up(hand, 12, 10)
    ring = finger_is_up(hand, 16, 14)
    pinky = finger_is_up(hand, 20, 18)

    # ----- Y -----
    # Thumb + pinky
    if (
        thumb
        and not index
        and not middle
        and not ring
        and pinky
    ):
        return "Y"

    # ----- L -----
    # Thumb + index
    if (
        thumb
        and index
        and not middle
        and not ring
        and not pinky
    ):
        return "L"

    # ----- I -----
    # Only pinky
    if (
        not thumb
        and not index
        and not middle
        and not ring
        and pinky
    ):
        return "I"

    # ----- B -----
    # Four fingers extended
    if (
        index
        and middle
        and ring
        and pinky
    ):
        return "B"

    # ----- A -----
    # Four fingers folded
    if (
        not index
        and not middle
        and not ring
        and not pinky
    ):
        return "A"

    return "Unknown"


def stabilize_prediction(prediction):
    """
    Only accept a prediction if the same result
    appears consistently in recent frames.
    """

    prediction_history.append(prediction)

    if len(prediction_history) < 5:
        return "Unknown"

    # Find most common prediction
    most_common = max(
        set(prediction_history),
        key=prediction_history.count
    )

    # Require at least 4 of the last 5 frames
    if prediction_history.count(most_common) >= 4:
        return most_common

    return "Unknown"


# ---------------- Main camera loop ----------------

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

    detected_letter = "None"

    # ---------------- Hand detected ----------------

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

        # Raw detection
        raw_letter = detect_asl_letter(hand)

        # Stabilized detection
        detected_letter = stabilize_prediction(raw_letter)

        current_time = time.time()

        # ---------------- Correct answer ----------------

        if detected_letter == target_letter:

            if correct_start_time is None:
                correct_start_time = current_time

            held_for = current_time - correct_start_time

            if held_for >= HOLD_TIME:

                score += 1

                message = "CORRECT!"
                message_until = current_time + 1.0

                # Choose a different target
                choices = [
                    letter
                    for letter in LETTERS
                    if letter != target_letter
                ]

                target_letter = random.choice(choices)

                correct_start_time = None

                # Clear old predictions so previous
                # letter does not affect the next one
                prediction_history.clear()

        else:
            correct_start_time = None

    else:

        correct_start_time = None
        prediction_history.clear()

    # ---------------- Interface ----------------

    cv2.putText(
        frame,
        "PhysiLearn - ASL Practice",
        (30, 45),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        f"TARGET: {target_letter}",
        (30, 100),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.4,
        (255, 255, 255),
        3
    )

    cv2.putText(
        frame,
        f"Detected: {detected_letter}",
        (30, 150),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        f"Score: {score}",
        (30, 195),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (255, 255, 255),
        2
    )

    # ---------------- Hold progress ----------------

    if correct_start_time is not None:

        progress = min(
            (time.time() - correct_start_time) / HOLD_TIME,
            1.0
        )

        cv2.putText(
            frame,
            f"Hold... {int(progress * 100)}%",
            (30, 240),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2
        )

    # ---------------- Correct message ----------------

    if time.time() < message_until:

        cv2.putText(
            frame,
            message,
            (30, 300),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.3,
            (0, 255, 0),
            3
        )

    cv2.imshow(
        "PhysiLearn - ASL Quiz",
        frame
    )

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


cap.release()
landmarker.close()
cv2.destroyAllWindows()