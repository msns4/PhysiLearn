import cv2
import json
import math
import time

WINDOW = "PhysiLearn - Toy Car Lab"
RULER_LENGTH_CM = 25.0
MIN_STEP_PX = 2.0  # Ignore tiny tracking jitter
MAX_STEP_PX = 100.0  # Reject implausible jumps between frames

pixels_per_cm = None
calibration_points = []
calibrating = False
tracker = None

recording = False
record_start = None
first_position = None
last_position = None
distance_cm = 0.0
measurements = []
latest_result = None
message = "Press 3 to calibrate"


def mouse_callback(event, x, y, flags, userdata):
    global calibrating, pixels_per_cm, message

    if event != cv2.EVENT_LBUTTONDOWN or not calibrating:
        return

    calibration_points.append((x, y))

    if len(calibration_points) == 2:
        length_px = math.dist(*calibration_points)
        if length_px < 20:
            calibration_points.clear()
            message = "Points too close - press 3 and retry"
            print(message)
            return

        pixels_per_cm = length_px / RULER_LENGTH_CM
        calibrating = False
        message = f"Calibrated: {pixels_per_cm:.2f} px/cm"
        print(message)


cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError("Could not open webcam")

cv2.namedWindow(WINDOW)
cv2.setMouseCallback(WINDOW, mouse_callback)

print("1: Select car | 2: Quit | 3: Calibrate | 4: Start/Stop recording")

while True:
    success, frame = cap.read()
    if not success:
        break

    currently_tracked = False

    if tracker is not None:
        tracked, box = tracker.update(frame)

        if tracked:
            currently_tracked = True
            x, y, w, h = map(int, box)
            center = (x + w / 2, y + h / 2)

            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.circle(frame, (int(center[0]), int(center[1])), 5, (0, 0, 255), -1)
            cv2.putText(frame, "TRACKING", (x, max(25, y - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            if recording:
                if first_position is None:
                    first_position = center
                    last_position = center

                step_px = math.dist(last_position, center)
                if step_px > MAX_STEP_PX:
                    recording = False
                    latest_result = None
                    message = "Tracking jumped - recording canceled"
                    print(message)
                else:
                    if step_px >= MIN_STEP_PX:
                        distance_cm += step_px / pixels_per_cm
                        last_position = center

                    elapsed = time.perf_counter() - record_start
                    measurements.append({
                        "time_s": round(elapsed, 3),
                        "x_px": round(center[0], 2),
                        "y_px": round(center[1], 2),
                    })
        else:
            if recording:
                recording = False
                latest_result = None
                message = "Tracking lost - recording canceled"
                print(message)
            cv2.putText(frame, "Tracking lost - press 1", (20, 125),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 255), 2)

    for point in calibration_points:
        cv2.circle(frame, point, 6, (255, 0, 255), -1)
    if len(calibration_points) == 2:
        cv2.line(frame, *calibration_points, (255, 0, 255), 2)

    cv2.putText(frame, "1: Select | 2: Quit | 3: Calibrate | 4: Record",
                (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (255, 255, 255), 2)

    if calibrating:
        status = "Click 0 cm, then 25 cm on the ruler"
    elif pixels_per_cm is None:
        status = "Not calibrated"
    else:
        status = f"Scale: {pixels_per_cm:.2f} px/cm"
    cv2.putText(frame, status, (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)

    if recording:
        duration = time.perf_counter() - record_start
        cv2.putText(frame, f"RECORDING: {duration:.1f} s", (20, 105),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.putText(frame, f"Distance: {distance_cm:.1f} cm", (20, 140),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    elif latest_result is not None:
        cv2.putText(frame, f"Distance: {latest_result['distance_cm']:.1f} cm", (20, 105),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.putText(frame, f"Avg speed: {latest_result['average_speed_cm_s']:.1f} cm/s", (20, 140),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    else:
        cv2.putText(frame, message, (20, 105),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0, 255, 255), 2)

    cv2.imshow(WINDOW, frame)
    key = cv2.waitKey(1) & 0xFF

    if key == ord("1"):
        if recording:
            print("Press 4 to stop recording before selecting a car")
            continue

        box = cv2.selectROI(WINDOW, frame, fromCenter=False, showCrosshair=True)
        cv2.setMouseCallback(WINDOW, mouse_callback)
        if box[2] > 0 and box[3] > 0:
            if hasattr(cv2, "TrackerCSRT_create"):
                tracker = cv2.TrackerCSRT_create()
            else:
                tracker = cv2.legacy.TrackerCSRT_create()
            tracker.init(frame, box)
            latest_result = None
            message = "Car selected - press 4 to record"

    elif key == ord("2"):
        break

    elif key == ord("3"):
        if recording:
            print("Press 4 to stop recording before calibration")
            continue
        calibrating = True
        calibration_points.clear()
        pixels_per_cm = None
        latest_result = None
        message = "Click 0 cm and 25 cm"
        print(message)

    elif key == ord("4"):
        if not recording:
            if pixels_per_cm is None or not currently_tracked:
                print("Calibrate (3) and select a visible car (1) first")
                continue

            recording = True
            record_start = time.perf_counter()
            first_position = None
            last_position = None
            distance_cm = 0.0
            measurements = []
            latest_result = None
            print("Recording started. Move the car, then press 4 again.")
        else:
            recording = False
            if len(measurements) < 2 or first_position is None:
                print("Not enough measurements - try again")
                continue

            duration = measurements[-1]["time_s"] - measurements[0]["time_s"]
            if duration <= 0:
                print("Recording too short - try again")
                continue

            displacement_cm = math.dist(first_position, last_position) / pixels_per_cm
            average_speed = distance_cm / duration
            latest_result = {
                "distance_cm": round(distance_cm, 2),
                "displacement_cm": round(displacement_cm, 2),
                "duration_s": round(duration, 2),
                "average_speed_cm_s": round(average_speed, 2),
                "pixels_per_cm": round(pixels_per_cm, 3),
                "samples": measurements,
            }

            with open("toy_car_recording.json", "w", encoding="utf-8") as f:
                json.dump(latest_result, f, indent=2)

            print("\n--- PHYSICS RESULTS ---")
            print(f"Distance: {distance_cm:.2f} cm")
            print(f"Displacement: {displacement_cm:.2f} cm")
            print(f"Time: {duration:.2f} s")
            print(f"Average speed: {average_speed:.2f} cm/s")
            print("Saved: toy_car_recording.json\n")

cap.release()
cv2.destroyAllWindows()
