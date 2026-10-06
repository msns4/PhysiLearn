import cv2
import numpy as np
from collections import deque


# ============================================================
# CAMERA
# ============================================================

CAMERA_INDEX = 0

cap = cv2.VideoCapture(CAMERA_INDEX)

# Try to request a reasonably large image.
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

if not cap.isOpened():
    raise RuntimeError("Could not open webcam.")


# ============================================================
# DEFAULT HSV RANGE
# ============================================================
#
# Starting estimate for a yellow-green tennis ball.
# We can tune these values for your room/light using sliders.
#

DEFAULT_LOWER_H = 25
DEFAULT_LOWER_S = 70
DEFAULT_LOWER_V = 70

DEFAULT_UPPER_H = 50
DEFAULT_UPPER_S = 255
DEFAULT_UPPER_V = 255


# ============================================================
# TRACKING SETTINGS
# ============================================================

MIN_RADIUS = 8
MIN_AREA = 250
MIN_CIRCULARITY = 0.40

SMOOTHING_FRAMES = 5

recent_centers = deque(
    maxlen=SMOOTHING_FRAMES
)

recent_radii = deque(
    maxlen=SMOOTHING_FRAMES
)


# ============================================================
# HSV CONTROL WINDOW
# ============================================================

cv2.namedWindow(
    "HSV Controls",
    cv2.WINDOW_NORMAL
)

cv2.resizeWindow(
    "HSV Controls",
    500,
    320
)


def nothing(value):
    pass


cv2.createTrackbar(
    "Lower H",
    "HSV Controls",
    DEFAULT_LOWER_H,
    179,
    nothing
)

cv2.createTrackbar(
    "Lower S",
    "HSV Controls",
    DEFAULT_LOWER_S,
    255,
    nothing
)

cv2.createTrackbar(
    "Lower V",
    "HSV Controls",
    DEFAULT_LOWER_V,
    255,
    nothing
)

cv2.createTrackbar(
    "Upper H",
    "HSV Controls",
    DEFAULT_UPPER_H,
    179,
    nothing
)

cv2.createTrackbar(
    "Upper S",
    "HSV Controls",
    DEFAULT_UPPER_S,
    255,
    nothing
)

cv2.createTrackbar(
    "Upper V",
    "HSV Controls",
    DEFAULT_UPPER_V,
    255,
    nothing
)


# ============================================================
# HELPERS
# ============================================================

def get_hsv_limits():

    lower = np.array(
        [
            cv2.getTrackbarPos(
                "Lower H",
                "HSV Controls"
            ),
            cv2.getTrackbarPos(
                "Lower S",
                "HSV Controls"
            ),
            cv2.getTrackbarPos(
                "Lower V",
                "HSV Controls"
            ),
        ],
        dtype=np.uint8
    )

    upper = np.array(
        [
            cv2.getTrackbarPos(
                "Upper H",
                "HSV Controls"
            ),
            cv2.getTrackbarPos(
                "Upper S",
                "HSV Controls"
            ),
            cv2.getTrackbarPos(
                "Upper V",
                "HSV Controls"
            ),
        ],
        dtype=np.uint8
    )

    return lower, upper


def reset_hsv():

    cv2.setTrackbarPos(
        "Lower H",
        "HSV Controls",
        DEFAULT_LOWER_H
    )

    cv2.setTrackbarPos(
        "Lower S",
        "HSV Controls",
        DEFAULT_LOWER_S
    )

    cv2.setTrackbarPos(
        "Lower V",
        "HSV Controls",
        DEFAULT_LOWER_V
    )

    cv2.setTrackbarPos(
        "Upper H",
        "HSV Controls",
        DEFAULT_UPPER_H
    )

    cv2.setTrackbarPos(
        "Upper S",
        "HSV Controls",
        DEFAULT_UPPER_S
    )

    cv2.setTrackbarPos(
        "Upper V",
        "HSV Controls",
        DEFAULT_UPPER_V
    )


def create_ball_mask(
    frame,
    lower,
    upper,
):

    blurred = cv2.GaussianBlur(
        frame,
        (11, 11),
        0
    )

    hsv = cv2.cvtColor(
        blurred,
        cv2.COLOR_BGR2HSV
    )

    mask = cv2.inRange(
        hsv,
        lower,
        upper
    )

    # Remove isolated noise.
    kernel = np.ones(
        (5, 5),
        np.uint8
    )

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_OPEN,
        kernel,
        iterations=2
    )

    # Fill small holes inside the ball.
    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_CLOSE,
        kernel,
        iterations=2
    )

    return mask


def find_ball(mask):

    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    best_candidate = None
    best_score = 0

    for contour in contours:

        area = cv2.contourArea(
            contour
        )

        if area < MIN_AREA:
            continue

        perimeter = cv2.arcLength(
            contour,
            True
        )

        if perimeter <= 0:
            continue

        circularity = (
            4
            * np.pi
            * area
            / (perimeter * perimeter)
        )

        if circularity < MIN_CIRCULARITY:
            continue

        (x, y), radius = cv2.minEnclosingCircle(
            contour
        )

        if radius < MIN_RADIUS:
            continue

        # Larger and more circular objects are preferred.
        score = area * circularity

        if score > best_score:

            best_score = score

            best_candidate = {
                "x": x,
                "y": y,
                "radius": radius,
                "area": area,
                "circularity": circularity,
            }

    return best_candidate


def smooth_detection(
    x,
    y,
    radius,
):

    recent_centers.append(
        (x, y)
    )

    recent_radii.append(
        radius
    )

    avg_x = np.mean(
        [
            point[0]
            for point in recent_centers
        ]
    )

    avg_y = np.mean(
        [
            point[1]
            for point in recent_centers
        ]
    )

    avg_radius = np.mean(
        recent_radii
    )

    return (
        avg_x,
        avg_y,
        avg_radius
    )


# ============================================================
# MAIN LOOP
# ============================================================

print()
print("----------------------------------")
print("PHYSILEARN BALL TRACKING TEST")
print("----------------------------------")
print("Show your tennis ball to the webcam.")
print()
print("Q / ESC = quit")
print("R       = reset HSV values")
print()
print("The white mask should mainly show")
print("the tennis ball, not the background.")
print("----------------------------------")
print()


while True:

    ret, frame = cap.read()

    if not ret:
        print("Could not read webcam frame.")
        break

    # Mirror the image so movement feels natural.
    frame = cv2.flip(
        frame,
        1
    )

    lower_hsv, upper_hsv = get_hsv_limits()

    mask = create_ball_mask(
        frame,
        lower_hsv,
        upper_hsv
    )

    ball = find_ball(
        mask
    )

    # --------------------------------------------------------
    # BALL FOUND
    # --------------------------------------------------------

    if ball is not None:

        x = ball["x"]
        y = ball["y"]
        radius = ball["radius"]

        x, y, radius = smooth_detection(
            x,
            y,
            radius
        )

        center = (
            int(x),
            int(y)
        )

        radius_int = int(
            radius
        )

        # Ball circle
        cv2.circle(
            frame,
            center,
            radius_int,
            (0, 255, 0),
            3
        )

        # Ball center
        cv2.circle(
            frame,
            center,
            5,
            (0, 0, 255),
            -1
        )

        # Crosshair
        cv2.line(
            frame,
            (
                center[0] - 15,
                center[1]
            ),
            (
                center[0] + 15,
                center[1]
            ),
            (255, 255, 255),
            1
        )

        cv2.line(
            frame,
            (
                center[0],
                center[1] - 15
            ),
            (
                center[0],
                center[1] + 15
            ),
            (255, 255, 255),
            1
        )

        cv2.putText(
            frame,
            "BALL DETECTED",
            (30, 45),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            f"X: {x:.1f} px",
            (30, 85),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"Y: {y:.1f} px",
            (30, 120),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"Radius: {radius:.1f} px",
            (30, 155),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            (
                f"Diameter: "
                f"{radius * 2:.1f} px"
            ),
            (30, 190),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (255, 255, 255),
            2
        )

    # --------------------------------------------------------
    # BALL NOT FOUND
    # --------------------------------------------------------

    else:

        recent_centers.clear()
        recent_radii.clear()

        cv2.putText(
            frame,
            "BALL NOT DETECTED",
            (30, 45),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 0, 255),
            2
        )

        cv2.putText(
            frame,
            "Adjust HSV sliders if needed",
            (30, 85),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )


    # --------------------------------------------------------
    # HSV VALUES ON SCREEN
    # --------------------------------------------------------

    cv2.putText(
        frame,
        (
            f"HSV lower: "
            f"{lower_hsv.tolist()}"
        ),
        (30, frame.shape[0] - 55),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        1
    )

    cv2.putText(
        frame,
        (
            f"HSV upper: "
            f"{upper_hsv.tolist()}"
        ),
        (30, frame.shape[0] - 25),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        1
    )


    # --------------------------------------------------------
    # WINDOWS
    # --------------------------------------------------------

    cv2.imshow(
        "PhysiLearn - Ball Tracking Test",
        frame
    )

    cv2.imshow(
        "Ball Mask",
        mask
    )


    # --------------------------------------------------------
    # KEYBOARD
    # --------------------------------------------------------

    key = cv2.waitKey(
        1
    ) & 0xFF

    if key == ord("q"):
        break

    if key == 27:
        break

    if key == ord("r"):
        reset_hsv()


# ============================================================
# CLEANUP
# ============================================================

cap.release()

cv2.destroyAllWindows()

print()
print("Ball tracking test finished.")