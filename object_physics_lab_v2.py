"""PhysiLearn — Universal Object Physics Lab, version 2.

Select an object name when starting the app (toy car, box, ball, custom).
Track a manually selected object using OpenCV CSRT.

Camera controls:
1 — select object with the mouse
2 — quit
3 — calibrate against a REAL 25-cm ruler (optional)
4 — start/stop recording
5 — return to pixel-only mode

Each completed run saves a new JSON file and a new graph in ./experiments/.
Without a real ruler, values are pixels and pixels/second, NOT centimeters.
"""

from pathlib import Path
from datetime import datetime
import cv2
import json
import math
import time

# Use a non-interactive backend so saving graphs never blocks the webcam window.
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

WINDOW = "PhysiLearn - Object Physics Lab"
RULER_LENGTH_CM = 25.0

# Tunable settings: stabilize the center and ignore very small movements.
SMOOTHING_ALPHA = 0.35       # 0 .. 1. Lower = more smoothing.
MIN_STEP_PX = 3.0            # Only add movements >= 3 px to total distance.
MAX_RAW_STEP_PX = 85.0       # Suspicious jump threshold, supplemented by object size and time.
RECOVERY_STABLE_FRAMES = 2  # Require stable frames before resuming after a gap.
CAMERA_WIDTH = 1280           # Restored original camera capture resolution.
CAMERA_HEIGHT = 720
SPEED_WINDOW_S = 0.40        # Average speed over the previous 0.4 seconds.

OUTPUT_DIR = Path(__file__).resolve().parent / "experiments"

OBJECT_OPTIONS = {
    "1": ("Toy Car", "toy_car"),
    "2": ("Box", "box"),
    "3": ("Tennis Ball", "tennis_ball"),
    "4": ("Custom Object", "custom_object"),
}

object_label = "Custom Object"
object_slug = "custom_object"


class TrackingGuard:
    """Pause, rather than destroy, a recording when the tracker becomes unreliable.

    A jump is NOT counted as motion. A new location is only accepted after the
    user explicitly re-selects a region; otherwise the object must return near
    the last trustworthy position. Missing motion cannot be reconstructed.
    """

    def __init__(self):
        self.paused = False
        self.gaps = 0
        self.skipped_frames = 0
        self.segment = 0
        self.last_good = None
        self.last_time = None
        self.recovery_candidate = None
        self.stable_count = 0
        self.manual_reselection = False
        self.message = ""

    def pause(self, reason):
        if not self.paused:
            self.gaps += 1
            print("Tracking warning:", reason, "— recording paused, not canceled")
        self.paused = True
        self.recovery_candidate = None
        self.stable_count = 0
        self.message = reason

    def reselect(self):
        self.pause("Object re-selected. Reacquiring tracking")
        self.manual_reselection = True
        self.last_good = None
        self.last_time = None

    def observe(self, center, size, now):
        """Return (accept_sample, new_segment). Called on each camera frame."""
        if center is None:
            self.pause("Object lost. Press 1 to select it again")
            self.skipped_frames += 1
            return False, False

        diagonal = math.hypot(float(size[0]), float(size[1]))
        elapsed = max(0.0, now - self.last_time) if self.last_time is not None else 0.0
        # A stalled frame can represent a real object displacement; do not
        # mistake ordinary slow FPS for an instant tracking jump.
        limit = max(MAX_RAW_STEP_PX, 1.25 * diagonal, min(220.0, 650.0 * elapsed))

        if not self.paused and self.last_good is not None:
            if math.dist(self.last_good, center) > limit:
                self.pause("Sudden tracking jump. Press 1 if the tracker moved to another object")

        if self.paused:
            self.skipped_frames += 1
            close_to_old = self.last_good is not None and math.dist(self.last_good, center) <= limit
            if self.manual_reselection or close_to_old:
                if self.recovery_candidate is None or math.dist(self.recovery_candidate, center) > limit:
                    self.stable_count = 1
                else:
                    self.stable_count += 1
                self.recovery_candidate = center
                if self.stable_count >= RECOVERY_STABLE_FRAMES:
                    self.paused = False
                    self.segment += 1
                    self.last_good = center
                    self.last_time = now
                    self.manual_reselection = False
                    self.message = "Tracking resumed. Motion during gaps was not measured"
                    self.recovery_candidate = None
                    self.stable_count = 0
                    return True, True
            else:
                self.recovery_candidate = None
                self.stable_count = 0
            return False, False

        self.last_good = center
        self.last_time = now
        return True, False


def choose_object():
    """Manually label this experiment; --object skips the console prompt."""
    import argparse
    global object_label, object_slug

    parser = argparse.ArgumentParser(description="PhysiLearn Object Physics Lab")
    parser.add_argument(
        "--object", choices=("1", "2", "3", "4"), default=None,
        help="1=Toy Car, 2=Box, 3=Tennis Ball, 4=Custom Object"
    )
    args = parser.parse_args()

    if args.object is not None:
        # Called from the PhysiLearn graphical object selector.
        choice = args.object
    else:
        # Backward-compatible direct terminal launch.
        print("\nSelect the object to study:")
        for key, (label, _) in OBJECT_OPTIONS.items():
            print(f"  {key} - {label}")
        choice = input("Enter 1/2/3/4 [default: 4]: ").strip() or "4"
        if choice not in OBJECT_OPTIONS:
            print("Unknown choice; using Custom Object.")
            choice = "4"

    object_label, object_slug = OBJECT_OPTIONS[choice]
    print(f"Object: {object_label}\n")


def create_result_paths():
    """Create unique filenames so a new run never replaces an earlier run."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    stem = f"{stamp}_{object_slug}"
    return OUTPUT_DIR / f"{stem}.json", OUTPUT_DIR / f"{stem}.png"

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
tracking_guard = TrackingGuard()
message = "Pixel mode: select object (1), then record (4)"


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
    global latest_result, message, path_px, last_accepted
    if len(samples) < 3:
        message = "Not enough measurements; record for longer"
        print(message)
        return

    # Include the final sub-threshold residual: ignoring it can make the
    # measured displacement slightly exceed the measured path on a clean run.
    if smoothed is not None and last_accepted is not None:
        tail = math.dist(last_accepted, smoothed)
        if tail > 1e-6:
            path_px += tail
            samples[-1]["cumulative_distance_px"] = round(path_px, 3)
            last_accepted = smoothed

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
    segment_ids = [s.get("tracking_segment", 0) for s in samples]
    segment_start = 0
    for i in range(len(samples)):
        if i and segment_ids[i] != segment_ids[i - 1]:
            segment_start = i
            j = i
        while j < i and t[i] - t[j] > SPEED_WINDOW_S:
            j += 1
        k = max(segment_start, j - 1)
        dt = t[i] - t[k]
        delta_path = (samples[i]["cumulative_distance_px"]
                      - samples[k]["cumulative_distance_px"])
        speed.append((delta_path / dt / scale) if dt > 1e-5 else 0.0)

    distance, dist_unit = format_value(total_px)
    displacement, _ = format_value(displacement_px)
    avg_speed, speed_unit = format_value(avg_speed_px_s, "speed")

    result_path, graph_path = create_result_paths()

    latest_result = {
        "object_name": object_label,
        "tracking_method": "OpenCV CSRT, manual bounding-box selection",
        "recorded_at_local": datetime.now().isoformat(timespec="seconds"),
        "measurement_units": unit,
        "calibration_used": pixels_per_cm is not None,
        "pixels_per_cm": pixels_per_cm,
        "distance": round(distance, 2),
        "displacement_magnitude": round(displacement, 2),
        "duration_s": round(duration, 2),
        "average_speed": round(avg_speed, 2),
        "position_x": "signed horizontal position relative to recording start",
        "speed_estimate_window_s": SPEED_WINDOW_S,
        "tracking_gap_count": tracking_guard.gaps,
        "tracking_skipped_frames": tracking_guard.skipped_frames,
        "tracking_quality_note": (
            "Tracking was interrupted. Unobserved motion is not counted in distance; "
            "the full path, speed and displacement/path ratio may be incomplete."
            if tracking_guard.gaps else
            "No tracking interruptions detected; webcam measurements remain approximate."
        ),
        "samples": samples,
    }

    result_path.write_text(
        json.dumps(latest_result, indent=2), encoding="utf-8"
    )

    fig, axes = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
    # Plot segments separately: never draw a fake motion line through a gap.
    for part in sorted(set(segment_ids)):
        indices = [i for i, value in enumerate(segment_ids) if value == part]
        if indices:
            axes[0].plot([t[i] for i in indices], [x_position[i] for i in indices], linewidth=1.8)
    axes[0].set_ylabel(f"Horizontal position ({unit})")
    axes[0].set_title(f"{object_label} - Motion Analysis")
    axes[0].grid(alpha=0.3)

    for part in sorted(set(segment_ids)):
        indices = [i for i, value in enumerate(segment_ids) if value == part]
        if indices:
            axes[1].plot([t[i] for i in indices], [speed[i] for i in indices], linewidth=1.8)
    axes[1].set_ylabel(f"Estimated speed ({unit}/s)")
    axes[1].set_xlabel("Time (s)")
    axes[1].grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(graph_path, dpi=150)
    plt.close(fig)

    print(f"\n--- {object_label.upper()} - PHYSICS RESULTS ---")
    print(f"Distance: {distance:.2f} {dist_unit}")
    print(f"Displacement magnitude: {displacement:.2f} {dist_unit}")
    print(f"Time: {duration:.2f} s")
    print(f"Average speed: {avg_speed:.2f} {speed_unit}")
    if pixels_per_cm is None:
        print("PIXEL MODE: these are image measurements, not centimeters.")
    print(f"Saved JSON: {result_path}")
    print(f"Saved graph: {graph_path}")
    if tracking_guard.gaps:
        print(f"CAUTION: {tracking_guard.gaps} tracking gap(s), "
              f"{tracking_guard.skipped_frames} skipped frame(s). "
              "Missing parts of the path were NOT guessed.")
    print()
    message = "Saved results; tracking gaps flagged" if tracking_guard.gaps else "Saved JSON and graphs"


def write_text(frame, text, y, color=(255, 255, 255), size=0.6):
    cv2.putText(frame, text, (20, y), cv2.FONT_HERSHEY_SIMPLEX,
                size, (0, 0, 0), 4, cv2.LINE_AA)
    cv2.putText(frame, text, (20, y), cv2.FONT_HERSHEY_SIMPLEX,
                size, color, 2, cv2.LINE_AA)


def run():
    global tracker, recording, record_start, samples, latest_result
    global last_raw, smoothed, last_accepted, path_px, message
    global calibrating, pixels_per_cm, tracking_guard

    choose_object()

    # MJPG and a lighter processing resolution can improve FPS on Windows.
    # Webcam drivers may ignore any of these best-effort settings.
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) if hasattr(cv2, "CAP_DSHOW") else cv2.VideoCapture(0)
    if not cap.isOpened():
        cap.release()
        cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    if not cap.isOpened():
        raise RuntimeError("Could not open webcam")

    # WINDOW_NORMAL scales the camera feed instead of leaving a small frame
    # in the upper-left corner of a maximized WINDOW_AUTOSIZE window.
    cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
    fullscreen = False
    try:
        cv2.setWindowProperty(WINDOW, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        fullscreen = True
    except cv2.error:
        cv2.resizeWindow(WINDOW, 1200, 800)
    cv2.setMouseCallback(WINDOW, mouse_callback)

    print("PhysiLearn - Universal Object Motion Lab")
    print("1: Select | 2: Quit | 3: Calibrate (ruler only) | 4: Record | 5: Pixel mode")

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            # Horizontal mirror toggle; apply before tracking and drawing.
            frame = cv2.flip(frame, 1)
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
                        accepted, fresh_segment = tracking_guard.observe(
                            current_center, (w, h), time.perf_counter())
                        if accepted:
                            if fresh_segment:
                                # Never connect the last position before a gap
                                # to the first position after recovery.
                                smoothed = None
                                last_accepted = None
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
                                "tracking_segment": tracking_guard.segment,
                            })
                elif recording:
                    tracking_guard.observe(None, (0, 0), time.perf_counter())

            for point in calibration_points:
                cv2.circle(frame, point, 5, (255, 0, 255), -1)
            if len(calibration_points) == 2:
                cv2.line(frame, *calibration_points, (255, 0, 255), 2)

            write_text(frame, "1: Select / Reselect | 2: Quit | 3: Ruler | 4: Record | 5: Pixels | F: Window", 35)
            write_text(frame, f"Object: {object_label}", 175, (255, 220, 130), 0.55)
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
                if tracking_guard.paused:
                    write_text(frame, "TRACKING PAUSED: press 1 to reselect object", 205, (0, 160, 255), 0.6)
                else:
                    write_text(frame, f"RECORDING: {duration:.1f} s", 105, (0, 0, 255))
                write_text(frame, f"Distance: {live_path:.1f} {live_unit}", 140,
                           (0, 255, 255))
                if tracking_guard.paused:
                    write_text(frame, f"Paused at {duration:.1f} s, earlier measurements kept", 105,
                               (0, 160, 255), 0.5)
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

            if key in (ord("f"), ord("F")):
                try:
                    fullscreen = not fullscreen
                    cv2.setWindowProperty(
                        WINDOW, cv2.WND_PROP_FULLSCREEN,
                        cv2.WINDOW_FULLSCREEN if fullscreen else cv2.WINDOW_NORMAL,
                    )
                    if not fullscreen:
                        cv2.resizeWindow(WINDOW, 1200, 800)
                except cv2.error:
                    print("Fullscreen toggle is not supported by this OpenCV build")
                continue

            if key == ord("1"):
                box = cv2.selectROI(WINDOW, frame,
                                    fromCenter=False, showCrosshair=True)
                cv2.setMouseCallback(WINDOW, mouse_callback)
                if box[2] > 0 and box[3] > 0:
                    if hasattr(cv2, "TrackerCSRT_create"):
                        tracker = cv2.TrackerCSRT_create()
                    else:
                        tracker = cv2.legacy.TrackerCSRT_create()
                    tracker.init(frame, box)
                    if recording:
                        tracking_guard.reselect()
                        message = "Object reselected. Recovering tracking; recording preserved"
                    else:
                        latest_result = None
                        message = "Object selected - press 4 to record"

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
                        print("Select a visible object (1) and finish calibration first")
                        continue
                    recording = True
                    tracking_guard = TrackingGuard()
                    record_start = time.perf_counter()
                    last_raw = None
                    smoothed = None
                    last_accepted = None
                    path_px = 0.0
                    samples = []
                    latest_result = None
                    print("Recording started. Move the object, then press 4 again.")
                else:
                    recording = False
                    analyze_and_save()

    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    run()
