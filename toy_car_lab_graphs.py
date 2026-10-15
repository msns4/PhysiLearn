"""PhysiLearn - Toy Car Lab: optional calibration, recording and graphs.

Controls
--------
1: select car with mouse
2: quit
3: calibrate against a real 25-cm ruler (optional)
4: start/stop recording
5: return to pixel-only mode

Before calibration the results are in px and px/s, NOT cm and cm/s.
"""

from pathlib import Path
import cv2
import json
import math
import time

# Use a non-interactive backend so saving graphs never blocks the webcam window.
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

WINDOW = "PhysiLearn - Toy Car Physics Lab"
RULER_LENGTH_CM = 25.0

# Tunable settings: stabilize the center and ignore very small movements.
SMOOTHING_ALPHA = 0.35       # 0 .. 1. Lower = more smoothing.
MIN_STEP_PX = 3.0            # Only add movements >= 3 px to total distance.
MAX_RAW_STEP_PX = 100.0      # Reject an obvious tracking jump between frames.
SPEED_WINDOW_S = 0.40        # Average speed over the previous 0.4 seconds.

OUTPUT_DIR = Path(__file__).resolve().parent

pixels_per_cm = None
calibration_points = []
calibrating = False
tracker = None
recording = False
record_start = None
samples = []
latest_result = None
last_raw = None
smoothed = None
last_accepted = None
path_px = 0.0
message = "Pixel mode: select car (1), then record (4)"


def mouse_callback(event, x, y, flags, userdata):
    global calibrating, pixels_per_cm, message
    if event != cv2.EVENT_LBUTTONDOWN or not calibrating:
        return

    calibration_points.append((x, y))
    if len(calibration_points) == 2:
        span_px = math.dist(*calibration_points)
        if span_px < 20:
            calibration_points.clear()
            message = "Points too close; try two ruler marks again"
            print(message)
            return
        pixels_per_cm = span_px / RULER_LENGTH_CM
        calibrating = False
        message = f"Calibrated: {pixels_per_cm:.2f} px/cm"
        print(message)
        print("Important: only valid if you clicked the actual 0- and 25-cm marks.")


def format_value(pixel_value, unit="distance"):
    """Return a displayed value and its physical / pixel units."""
    if pixels_per_cm is None:
        return pixel_value, ("px" if unit == "distance" else "px/s")
    return pixel_value / pixels_per_cm, ("cm" if unit == "distance" else "cm/s")


def cancel_recording(reason):
    global recording, latest_result, samples, message
    recording = False
    latest_result = None
    samples = []
    message = reason
    print(reason)


def analyze_and_save():
    """Analyze tracked positions and create JSON and two physics graphs."""
    global latest_result, message
    if len(samples) < 3:
        message = "Not enough measurements; record for longer"
        print(message)
        return

    duration = samples[-1]["time_s"] - samples[0]["time_s"]
    if duration <= 0.05:
        message = "Recording too short"
        print(message)
        return

    start = (samples[0]["x_px"], samples[0]["y_px"])
    end = (samples[-1]["x_px"], samples[-1]["y_px"])
    total_px = samples[-1]["cumulative_distance_px"]
    displacement_px = math.dist(start, end)
    avg_speed_px_s = total_px / duration

    scale = pixels_per_cm if pixels_per_cm is not None else 1.0
    unit = "cm" if pixels_per_cm is not None else "px"
    t = [s["time_s"] - samples[0]["time_s"] for s in samples]
    x_position = [(s["x_px"] - start[0]) / scale for s in samples]
    speed = []

    # Speed is estimated from the increase in traveled distance over a short
    # moving window. This is more robust than differentiating adjacent frames.
    j = 0
    for i in range(len(samples)):
        while j < i and t[i] - t[j] > SPEED_WINDOW_S:
            j += 1
        k = max(0, j - 1)
        dt = t[i] - t[k]
        delta_path = (samples[i]["cumulative_distance_px"]
                      - samples[k]["cumulative_distance_px"])
        speed.append((delta_path / dt / scale) if dt > 1e-5 else 0.0)

    distance, dist_unit = format_value(total_px)
    displacement, _ = format_value(displacement_px)
    avg_speed, speed_unit = format_value(avg_speed_px_s, "speed")

    latest_result = {
        "measurement_units": unit,
        "calibration_used": pixels_per_cm is not None,
        "pixels_per_cm": pixels_per_cm,
        "distance": round(distance, 2),
        "displacement_magnitude": round(displacement, 2),
        "duration_s": round(duration, 2),
        "average_speed": round(avg_speed, 2),
        "position_x": "signed horizontal position relative to recording start",
        "speed_estimate_window_s": SPEED_WINDOW_S,
        "samples": samples,
    }

    result_path = OUTPUT_DIR / "toy_car_recording.json"
    result_path.write_text(
        json.dumps(latest_result, indent=2), encoding="utf-8"
    )

    fig, axes = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
    axes[0].plot(t, x_position, linewidth=1.8)
    axes[0].set_ylabel(f"Horizontal position ({unit})")
    axes[0].set_title("Toy Car - Motion Analysis")
    axes[0].grid(alpha=0.3)

    axes[1].plot(t, speed, linewidth=1.8)
    axes[1].set_ylabel(f"Estimated speed ({unit}/s)")
    axes[1].set_xlabel("Time (s)")
    axes[1].grid(alpha=0.3)
    fig.tight_layout()
    graph_path = OUTPUT_DIR / "toy_car_motion_graphs.png"
    fig.savefig(graph_path, dpi=150)
    plt.close(fig)

    print("\n--- PHYSICS RESULTS ---")
    print(f"Distance: {distance:.2f} {dist_unit}")
    print(f"Displacement magnitude: {displacement:.2f} {dist_unit}")
    print(f"Time: {duration:.2f} s")
    print(f"Average speed: {avg_speed:.2f} {speed_unit}")
    if pixels_per_cm is None:
        print("PIXEL MODE: these are image measurements, not centimeters.")
    print(f"Saved: {result_path.name}")
    print(f"Saved: {graph_path.name}\n")
    message = "Saved JSON and graphs"


def write_text(frame, text, y, color=(255, 255, 255), size=0.6):
    cv2.putText(frame, text, (20, y), cv2.FONT_HERSHEY_SIMPLEX,
                size, (0, 0, 0), 4, cv2.LINE_AA)
    cv2.putText(frame, text, (20, y), cv2.FONT_HERSHEY_SIMPLEX,
                size, color, 2, cv2.LINE_AA)


def run():
    global tracker, recording, record_start, samples, latest_result
    global last_raw, smoothed, last_accepted, path_px, message
    global calibrating, pixels_per_cm

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Could not open webcam")

    cv2.namedWindow(WINDOW)
    cv2.setMouseCallback(WINDOW, mouse_callback)

    print("PhysiLearn - Toy Car Motion Analysis")
    print("1: Select | 2: Quit | 3: Calibrate (ruler only) | 4: Record | 5: Pixel mode")

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            currently_tracked = False
            current_center = None

            if tracker is not None:
                tracked, box = tracker.update(frame)
                if tracked:
                    currently_tracked = True
                    x, y, w, h = map(int, box)
                    current_center = (x + w / 2, y + h / 2)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.circle(frame, (int(current_center[0]), int(current_center[1])),
                               5, (0, 0, 255), -1)
                    write_text(frame, "TRACKING", 205, (0, 255, 0), 0.5)

                    if recording:
                        if last_raw is not None:
                            raw_jump = math.dist(last_raw, current_center)
                            if raw_jump > MAX_RAW_STEP_PX:
                                cancel_recording("Tracking jumped - recording canceled")

                        if recording:
                            last_raw = current_center
                            if smoothed is None:
                                smoothed = current_center
                                last_accepted = smoothed
                            else:
                                smoothed = (
                                    SMOOTHING_ALPHA * current_center[0]
                                    + (1 - SMOOTHING_ALPHA) * smoothed[0],
                                    SMOOTHING_ALPHA * current_center[1]
                                    + (1 - SMOOTHING_ALPHA) * smoothed[1],
                                )
                                step = math.dist(last_accepted, smoothed)
                                if step >= MIN_STEP_PX:
                                    path_px += step
                                    last_accepted = smoothed

                            samples.append({
                                "time_s": round(time.perf_counter() - record_start, 4),
                                "x_px": round(smoothed[0], 3),
                                "y_px": round(smoothed[1], 3),
                                "cumulative_distance_px": round(path_px, 3),
                            })
                elif recording:
                    cancel_recording("Tracking lost - recording canceled")

            for point in calibration_points:
                cv2.circle(frame, point, 5, (255, 0, 255), -1)
            if len(calibration_points) == 2:
                cv2.line(frame, *calibration_points, (255, 0, 255), 2)

            write_text(frame, "1: Select | 2: Quit | 3: Ruler | 4: Record | 5: Pixels", 35)
            if calibrating:
                write_text(frame, "Click real 0-cm and 25-cm marks", 70, (0, 255, 255))
            elif pixels_per_cm is None:
                write_text(frame, "PIXEL MODE (no ruler needed)", 70, (0, 255, 255))
            else:
                write_text(frame, f"CALIBRATED: {pixels_per_cm:.2f} px/cm", 70,
                           (0, 255, 255))

            if recording:
                duration = time.perf_counter() - record_start
                live_path, live_unit = format_value(path_px)
                write_text(frame, f"RECORDING: {duration:.1f} s", 105, (0, 0, 255))
                write_text(frame, f"Distance: {live_path:.1f} {live_unit}", 140,
                           (0, 255, 255))
            elif latest_result:
                unit = latest_result["measurement_units"]
                write_text(frame, f"Distance: {latest_result['distance']:.1f} {unit}",
                           105, (0, 255, 255))
                write_text(frame,
                           f"Avg speed: {latest_result['average_speed']:.1f} {unit}/s",
                           140, (0, 255, 255))
            else:
                write_text(frame, message, 105, (0, 255, 255), 0.52)

            cv2.imshow(WINDOW, frame)
            key = cv2.waitKey(1) & 0xFF

            if key == ord("1"):
                if recording:
                    print("Finish recording (4) first")
                    continue
                box = cv2.selectROI(WINDOW, frame,
                                    fromCenter=False, showCrosshair=True)
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
                    print("Finish recording (4) first")
                    continue
                calibrating = True
                calibration_points.clear()
                pixels_per_cm = None
                latest_result = None
                message = "Click the real 0- and 25-cm ruler marks"
                print(message)

            elif key == ord("5"):
                if recording:
                    print("Finish recording (4) first")
                    continue
                pixels_per_cm = None
                calibrating = False
                calibration_points.clear()
                latest_result = None
                message = "Pixel mode enabled (no ruler needed)"
                print(message)

            elif key == ord("4"):
                if not recording:
                    if not currently_tracked or calibrating:
                        print("Select a visible car (1) and finish calibration first")
                        continue
                    recording = True
                    record_start = time.perf_counter()
                    last_raw = None
                    smoothed = None
                    last_accepted = None
                    path_px = 0.0
                    samples = []
                    latest_result = None
                    print("Recording started. Move the car, then press 4 again.")
                else:
                    recording = False
                    analyze_and_save()

    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    run()
