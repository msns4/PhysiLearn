import json
import cv2
import numpy as np
import matplotlib.pyplot as plt
import time
from collections import deque


# ============================================================
# PHYSILEARN BALL PHYSICS TEST
# ============================================================

# Approximate diameter of a standard tennis ball.
# Used only to estimate real-world scale.
BALL_DIAMETER_M = 0.067

CAMERA_INDEX = 0

CALIBRATION_SECONDS = 2.5
COUNTDOWN_SECONDS = 3
RECORDING_SECONDS = 4.0


# ============================================================
# HSV RANGE
# ============================================================
#
# These values already worked well for your tennis ball.
#

LOWER_HSV = np.array(
    [25, 70, 70],
    dtype=np.uint8
)

UPPER_HSV = np.array(
    [50, 255, 255],
    dtype=np.uint8
)


# ============================================================
# BALL DETECTION SETTINGS
# ============================================================

MIN_RADIUS = 8
MIN_AREA = 250
MIN_CIRCULARITY = 0.40

CENTER_SMOOTHING = 5

recent_centers = deque(
    maxlen=CENTER_SMOOTHING
)

recent_radii = deque(
    maxlen=CENTER_SMOOTHING
)


# ============================================================
# CAMERA
# ============================================================

cap = cv2.VideoCapture(
    CAMERA_INDEX
)

cap.set(
    cv2.CAP_PROP_FRAME_WIDTH,
    1280
)

cap.set(
    cv2.CAP_PROP_FRAME_HEIGHT,
    720
)

if not cap.isOpened():
    raise RuntimeError(
        "Could not open webcam."
    )


# ============================================================
# HELPERS
# ============================================================

def create_ball_mask(frame):

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
        LOWER_HSV,
        UPPER_HSV
    )

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
            / (
                perimeter
                * perimeter
            )
        )

        if circularity < MIN_CIRCULARITY:
            continue

        (x, y), radius = (
            cv2.minEnclosingCircle(
                contour
            )
        )

        if radius < MIN_RADIUS:
            continue

        score = (
            area
            * circularity
        )

        if score > best_score:

            best_score = score

            best_candidate = {
                "x": float(x),
                "y": float(y),
                "radius": float(radius),
                "area": float(area),
                "circularity": float(
                    circularity
                ),
            }

    return best_candidate


def smooth_ball(
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

    smooth_x = np.mean(
        [
            point[0]
            for point
            in recent_centers
        ]
    )

    smooth_y = np.mean(
        [
            point[1]
            for point
            in recent_centers
        ]
    )

    smooth_radius = np.mean(
        recent_radii
    )

    return (
        float(smooth_x),
        float(smooth_y),
        float(smooth_radius),
    )


def reset_smoothing():

    recent_centers.clear()
    recent_radii.clear()


def draw_ball(
    frame,
    x,
    y,
    radius,
):

    center = (
        int(x),
        int(y)
    )

    radius_int = int(
        radius
    )

    cv2.circle(
        frame,
        center,
        radius_int,
        (0, 255, 0),
        3
    )

    cv2.circle(
        frame,
        center,
        5,
        (0, 0, 255),
        -1
    )

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


def moving_average(
    values,
    window=5,
):

    values = np.asarray(
        values,
        dtype=float
    )

    if len(values) < window:
        return values

    kernel = (
        np.ones(window)
        / window
    )

    padded = np.pad(
        values,
        (
            window // 2,
            window // 2
        ),
        mode="edge"
    )

    smoothed = np.convolve(
        padded,
        kernel,
        mode="valid"
    )

    return smoothed[
        :len(values)
    ]


# ============================================================
# STAGE 1 — CALIBRATION
# ============================================================

print()
print("------------------------------------------")
print("PHYSILEARN BALL PHYSICS EXPERIMENT")
print("------------------------------------------")
print()
print("STEP 1: CALIBRATION")
print()
print(
    "Hold the tennis ball still where it will roll."
)
print(
    "Keep it approximately the same distance from"
)
print(
    "the camera during the experiment."
)
print()
print("------------------------------------------")
print()


calibration_radii = []

calibration_start = None


while True:

    ret, frame = cap.read()

    if not ret:
        raise RuntimeError(
            "Could not read webcam frame."
        )

    frame = cv2.flip(
        frame,
        1
    )

    mask = create_ball_mask(
        frame
    )

    ball = find_ball(
        mask
    )

    if ball is not None:

        x, y, radius = smooth_ball(
            ball["x"],
            ball["y"],
            ball["radius"],
        )

        draw_ball(
            frame,
            x,
            y,
            radius
        )

        if calibration_start is None:

            calibration_start = (
                time.perf_counter()
            )

            calibration_radii = []

        elapsed = (
            time.perf_counter()
            - calibration_start
        )

        calibration_radii.append(
            radius
        )

        remaining = max(
            0.0,
            CALIBRATION_SECONDS
            - elapsed
        )

        cv2.putText(
            frame,
            "CALIBRATING BALL SIZE",
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            (
                f"Hold still: "
                f"{remaining:.1f}s"
            ),
            (30, 95),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.85,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            (
                f"Radius: "
                f"{radius:.1f} px"
            ),
            (30, 135),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

        if (
            elapsed
            >= CALIBRATION_SECONDS
        ):
            break

    else:

        reset_smoothing()

        calibration_start = None

        calibration_radii = []

        cv2.putText(
            frame,
            "SHOW TENNIS BALL",
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 0, 255),
            2
        )

        cv2.putText(
            frame,
            (
                "Hold the ball still "
                "in the motion plane"
            ),
            (30, 95),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

    cv2.imshow(
        "PhysiLearn - Ball Physics",
        frame
    )

    cv2.imshow(
        "Ball Mask",
        mask
    )

    key = (
        cv2.waitKey(1)
        & 0xFF
    )

    if (
        key == 27
        or key == ord("q")
    ):

        cap.release()
        cv2.destroyAllWindows()
        raise SystemExit


# ============================================================
# CALCULATE SCALE
# ============================================================

median_radius_px = float(
    np.median(
        calibration_radii
    )
)

median_diameter_px = (
    2.0
    * median_radius_px
)

meters_per_pixel = (
    BALL_DIAMETER_M
    / median_diameter_px
)


print(
    f"Ball diameter in image: "
    f"{median_diameter_px:.1f} px"
)

print(
    f"Estimated scale: "
    f"{meters_per_pixel:.6f} m/px"
)

print()


# ============================================================
# STAGE 2 — COUNTDOWN
# ============================================================

reset_smoothing()

countdown_start = (
    time.perf_counter()
)


while True:

    ret, frame = cap.read()

    if not ret:
        break

    frame = cv2.flip(
        frame,
        1
    )

    mask = create_ball_mask(
        frame
    )

    ball = find_ball(
        mask
    )

    if ball is not None:

        x, y, radius = smooth_ball(
            ball["x"],
            ball["y"],
            ball["radius"],
        )

        draw_ball(
            frame,
            x,
            y,
            radius
        )

    elapsed = (
        time.perf_counter()
        - countdown_start
    )

    remaining = int(
        np.ceil(
            COUNTDOWN_SECONDS
            - elapsed
        )
    )

    if remaining <= 0:
        break

    cv2.putText(
        frame,
        "GET READY",
        (30, 55),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.1,
        (255, 255, 255),
        3
    )

    cv2.putText(
        frame,
        str(remaining),
        (
            frame.shape[1] // 2 - 30,
            frame.shape[0] // 2
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        3.0,
        (0, 255, 255),
        6
    )

    cv2.putText(
        frame,
        "Roll the ball left to right",
        (30, 105),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2
    )

    cv2.imshow(
        "PhysiLearn - Ball Physics",
        frame
    )

    cv2.imshow(
        "Ball Mask",
        mask
    )

    key = (
        cv2.waitKey(1)
        & 0xFF
    )

    if (
        key == 27
        or key == ord("q")
    ):

        cap.release()
        cv2.destroyAllWindows()
        raise SystemExit


# ============================================================
# STAGE 3 — RECORD MOTION
# ============================================================

reset_smoothing()

times = []
xs_px = []
ys_px = []
radii_px = []

recording_start = (
    time.perf_counter()
)


while True:

    ret, frame = cap.read()

    if not ret:
        break

    frame = cv2.flip(
        frame,
        1
    )

    mask = create_ball_mask(
        frame
    )

    ball = find_ball(
        mask
    )

    current_time = (
        time.perf_counter()
    )

    elapsed = (
        current_time
        - recording_start
    )

    if (
        elapsed
        >= RECORDING_SECONDS
    ):
        break

    if ball is not None:

        x, y, radius = smooth_ball(
            ball["x"],
            ball["y"],
            ball["radius"],
        )

        draw_ball(
            frame,
            x,
            y,
            radius
        )

        times.append(
            elapsed
        )

        xs_px.append(
            x
        )

        ys_px.append(
            y
        )

        radii_px.append(
            radius
        )

        status_color = (
            0,
            255,
            0
        )

        status_text = (
            "BALL TRACKED"
        )

    else:

        reset_smoothing()

        status_color = (
            0,
            0,
            255
        )

        status_text = (
            "BALL LOST"
        )

    time_left = max(
        0.0,
        RECORDING_SECONDS
        - elapsed
    )

    cv2.putText(
        frame,
        "RECORDING",
        (30, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.1,
        (0, 0, 255),
        3
    )

    cv2.putText(
        frame,
        status_text,
        (30, 95),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        status_color,
        2
    )

    cv2.putText(
        frame,
        (
            f"Time left: "
            f"{time_left:.1f}s"
        ),
        (30, 135),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        (255, 255, 255),
        2
    )

    cv2.imshow(
        "PhysiLearn - Ball Physics",
        frame
    )

    cv2.imshow(
        "Ball Mask",
        mask
    )

    key = (
        cv2.waitKey(1)
        & 0xFF
    )

    if (
        key == 27
        or key == ord("q")
    ):
        break


# ============================================================
# CLEAN CAMERA WINDOWS
# ============================================================

cap.release()

cv2.destroyAllWindows()


# ============================================================
# CHECK DATA
# ============================================================

if len(times) < 20:

    print()
    print(
        "Not enough ball tracking data."
    )

    print(
        "Try again while keeping the ball visible."
    )

    raise SystemExit


# ============================================================
# CONVERT TO NUMPY
# ============================================================

times = np.asarray(
    times,
    dtype=float
)

xs_px = np.asarray(
    xs_px,
    dtype=float
)

ys_px = np.asarray(
    ys_px,
    dtype=float
)

radii_px = np.asarray(
    radii_px,
    dtype=float
)


# ============================================================
# SMOOTH POSITION
# ============================================================

xs_px_smooth = moving_average(
    xs_px,
    window=7
)

ys_px_smooth = moving_average(
    ys_px,
    window=7
)


# ============================================================
# CONVERT PIXELS TO ESTIMATED METERS
# ============================================================

x_m = (
    xs_px_smooth
    - xs_px_smooth[0]
) * meters_per_pixel

y_m = (
    ys_px_smooth
    - ys_px_smooth[0]
) * meters_per_pixel


# ============================================================
# REMOVE START / END STILLNESS
# ============================================================
#
# We estimate when the ball actually started moving.
#

dx_px = np.abs(
    np.diff(
        xs_px_smooth
    )
)

motion_threshold_px = 1.2

moving_indices = np.where(
    dx_px
    > motion_threshold_px
)[0]


if len(moving_indices) >= 5:

    first_motion = max(
        0,
        int(moving_indices[0])
        - 1
    )

    last_motion = min(
        len(times) - 1,
        int(moving_indices[-1])
        + 2
    )

else:

    first_motion = 0
    last_motion = (
        len(times) - 1
    )


experiment_times = (
    times[
        first_motion:
        last_motion + 1
    ]
)

experiment_x = (
    x_m[
        first_motion:
        last_motion + 1
    ]
)

experiment_y = (
    y_m[
        first_motion:
        last_motion + 1
    ]
)


# Reset experiment time to zero.

experiment_times = (
    experiment_times
    - experiment_times[0]
)


# ============================================================
# DISTANCE AND DISPLACEMENT
# ============================================================

dx = np.diff(
    experiment_x
)

dy = np.diff(
    experiment_y
)

step_distances = np.sqrt(
    dx ** 2
    + dy ** 2
)


# Ignore extremely tiny position changes caused by pixel noise.

noise_floor_m = (
    meters_per_pixel
    * 1.0
)

step_distances[
    step_distances
    < noise_floor_m
] = 0.0


distance_traveled = float(
    np.sum(
        step_distances
    )
)

horizontal_displacement = float(
    experiment_x[-1]
    - experiment_x[0]
)

total_time = float(
    experiment_times[-1]
)


# ============================================================
# SPEED / VELOCITY
# ============================================================

if total_time > 0:

    average_speed = (
        distance_traveled
        / total_time
    )

    average_velocity = (
        horizontal_displacement
        / total_time
    )

else:

    average_speed = 0.0
    average_velocity = 0.0


# ============================================================
# INSTANTANEOUS VELOCITY / ACCELERATION
# ============================================================

velocity = np.gradient(
    experiment_x,
    experiment_times
)

velocity = moving_average(
    velocity,
    window=7
)

acceleration = np.gradient(
    velocity,
    experiment_times
)

acceleration = moving_average(
    acceleration,
    window=9
)


# ============================================================
# CAMERA-SCALE QUALITY CHECK
# ============================================================

median_recording_radius = float(
    np.median(
        radii_px
    )
)

radius_change_percent = (
    np.std(
        radii_px
    )
    / median_recording_radius
    * 100
)

# ============================================================
# SAVE EXPERIMENT RESULT
# ============================================================

result_data = {
    "distance_traveled": round(distance_traveled, 4),
    "horizontal_displacement": round(horizontal_displacement, 4),
    "motion_time": round(total_time, 4),
    "average_speed": round(average_speed, 4),
    "average_velocity": round(average_velocity, 4),
    "meters_per_pixel": round(meters_per_pixel, 7),
    "ball_size_variation_percent": round(radius_change_percent, 2),
}

with open(
    "ball_experiment_result.json",
    "w",
    encoding="utf-8",
) as file:
    json.dump(
        result_data,
        file,
        indent=4,
    )

print(
    "Ball experiment result saved "
    "to ball_experiment_result.json."
)
# ============================================================
# RESULTS
# ============================================================

print()
print("------------------------------------------")
print("PHYSILEARN BALL EXPERIMENT")
print("------------------------------------------")
print()

print(
    "Estimated measurements"
)

print(
    "(camera-based calibration)"
)

print()

print(
    f"Tracked data points:     "
    f"{len(times)}"
)

print(
    f"Ball diameter:           "
    f"{BALL_DIAMETER_M:.3f} m"
)

print(
    f"Calibration diameter:    "
    f"{median_diameter_px:.1f} px"
)

print(
    f"Estimated scale:         "
    f"{meters_per_pixel:.6f} m/px"
)

print()

print(
    f"Distance traveled:       "
    f"{distance_traveled:.3f} m"
)

print(
    f"Horizontal displacement: "
    f"{horizontal_displacement:+.3f} m"
)

print(
    f"Motion time:             "
    f"{total_time:.3f} s"
)

print()

print(
    "AVERAGE SPEED"
)

print(
    "v = d / t"
)

print(
    f"v = "
    f"{distance_traveled:.3f} / "
    f"{total_time:.3f}"
)

print(
    f"v = "
    f"{average_speed:.3f} m/s"
)

print()

print(
    f"Average velocity:        "
    f"{average_velocity:+.3f} m/s"
)

print()

print(
    f"Ball-size variation:     "
    f"{radius_change_percent:.1f}%"
)

if radius_change_percent > 15:

    print()
    print(
        "WARNING:"
    )

    print(
        "The ball changed apparent size noticeably."
    )

    print(
        "Keep the ball at a more constant distance "
        "from the camera for better real-world estimates."
    )

print()
print("------------------------------------------")


# ============================================================
# EDUCATIONAL SUMMARY
# ============================================================

print()
print("PHYSICS")
print()

print(
    "Average speed tells us how much distance"
)

print(
    "the ball traveled per unit of time."
)

print()

print(
    "v = d / t"
)

print()

print(
    "Average velocity uses displacement instead"
)

print(
    "of total distance, so direction matters."
)

print()


# ============================================================
# GRAPHS
# ============================================================

# Position vs Time

plt.figure()

plt.plot(
    experiment_times,
    experiment_x
)

plt.xlabel(
    "Time (s)"
)

plt.ylabel(
    "Horizontal Position (m)"
)

plt.title(
    "Position vs Time"
)

plt.grid(
    True,
    alpha=0.3
)


# Velocity vs Time

plt.figure()

plt.plot(
    experiment_times,
    velocity
)

plt.axhline(
    0,
    linewidth=1
)

plt.xlabel(
    "Time (s)"
)

plt.ylabel(
    "Horizontal Velocity (m/s)"
)

plt.title(
    "Velocity vs Time"
)

plt.grid(
    True,
    alpha=0.3
)


# Acceleration vs Time

plt.figure()

plt.plot(
    experiment_times,
    acceleration
)

plt.axhline(
    0,
    linewidth=1
)

plt.xlabel(
    "Time (s)"
)

plt.ylabel(
    "Horizontal Acceleration (m/s²)"
)

plt.title(
    "Acceleration vs Time"
)

plt.grid(
    True,
    alpha=0.3
)


plt.show()