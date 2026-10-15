"""PhysiLearn — Ramp Physics Lab (experimental prototype).

Requires: opencv-contrib-python, numpy, matplotlib (already used by PhysiLearn).
Run from PhysiLearn-Eureka: .\\.venv\\Scripts\\python.exe ramp_physics_lab.py

Camera: fixed, looking SIDE-ON at a low, stable ramp. Keep car visible.
Controls in camera window:
  3 - mark ramp direction: click TOP, then BOTTOM in the camera image
  1 - select toy car bounding box (drag ROI, Enter)
  4 - start / stop recording
  5 - clear ramp points and selection (not during recording)
  2 - quit

Prototype works in PIXELS, not centimeters. Speed and acceleration are
image-space estimates, not calibrated physical measurements. Camera motion,
tracking jumps, perspective and manual pushing can distort estimates.
"""
from __future__ import annotations

import json
import math
import time
from collections import deque
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent
OUT = BASE / "experiments" / "ramp"
WINDOW = "PhysiLearn - Ramp Physics Lab"
SMOOTH_ALPHA = 0.4
MAX_JUMP_PX = 95
VELOCITY_WINDOW_S = 0.45


def project(point, top, bottom):
    """Signed pixel displacement along the TOP -> BOTTOM ramp direction."""
    direction = np.asarray(bottom, dtype=float) - np.asarray(top, dtype=float)
    length = float(np.linalg.norm(direction))
    if length < 30:
        raise ValueError("Ramp points are too close")
    unit = direction / length
    return float(np.dot(np.asarray(point, dtype=float) - np.asarray(top, dtype=float), unit))


def local_slope(times, positions, half_window=VELOCITY_WINDOW_S / 2):
    """Local linear regression for signed along-ramp velocity (px/s)."""
    t = np.asarray(times, dtype=float)
    p = np.asarray(positions, dtype=float)
    speeds = np.zeros(len(t), dtype=float)
    for i in range(len(t)):
        ids = np.flatnonzero(np.abs(t - t[i]) <= half_window)
        if len(ids) < 3:
            continue
        tx = t[ids] - np.mean(t[ids])
        denom = float(np.dot(tx, tx))
        if denom > 1e-8:
            speeds[i] = float(np.dot(tx, p[ids] - np.mean(p[ids])) / denom)
    return speeds


def analyze(samples, prediction):
    """Analyze position projected on the ramp, without asserting physical units."""
    if len(samples) < 12:
        raise ValueError("Not enough tracking samples")
    t = np.asarray([s["time_s"] for s in samples], dtype=float)
    t = t - t[0]
    p = np.asarray([s["along_ramp_px"] for s in samples], dtype=float)
    p = p - p[0]
    if t[-1] < 0.7:
        raise ValueError("Recording too short; record at least 1 second")
    v = local_slope(t, p)
    # Choose central, down-ramp motion samples for a qualitative trend only.
    # Exclude near-zero motion and the endpoints of the recording.
    motion_threshold = max(8.0, float(np.percentile(np.abs(v), 75)) * 0.15)
    active = (v > motion_threshold) & (t > t[-1] * 0.05) & (t < t[-1] * 0.95)
    active_ids = np.flatnonzero(active)
    trend = None
    if len(active_ids) >= 10 and t[active_ids[-1]] - t[active_ids[0]] >= 0.5:
        # Regression of signed along-ramp speed against time, px/s^2.
        tt = t[active_ids]
        vv = v[active_ids]
        centered = tt - np.mean(tt)
        trend = float(np.dot(centered, vv - np.mean(vv)) / np.dot(centered, centered))
    # Position may be negative if the car moves uphill or the ramp was clicked in reverse.
    displacement = float(p[-1])
    traveled = float(np.sum(np.abs(np.diff(p))))  # rough, noise-sensitive estimate
    if trend is None:
        assessment = "INCONCLUSIVE: not enough consistent downhill motion for a trend."
    elif trend > 10:
        assessment = "OBSERVED: estimated downhill speed generally increased."
    elif trend < -10:
        assessment = "OBSERVED: estimated downhill speed generally decreased."
    else:
        assessment = "OBSERVED: no clear speed increase in this recording."
    return {
        "duration_s": round(float(t[-1]), 3),
        "along_ramp_displacement_px": round(displacement, 2),
        "approx_along_ramp_path_px": round(traveled, 2),
        "estimated_downhill_speed_trend_px_s2": None if trend is None else round(trend, 2),
        "prediction": prediction,
        "assessment": assessment,
        "units": "pixels (image-space, uncalibrated)",
        "time": t.tolist(), "position": p.tolist(), "velocity": v.tolist(),
    }


def draw_text(frame, line, y, color=(255, 255, 255)):
    cv2.putText(frame, line, (16, y), cv2.FONT_HERSHEY_SIMPLEX, .54, (0, 0, 0), 4, cv2.LINE_AA)
    cv2.putText(frame, line, (16, y), cv2.FONT_HERSHEY_SIMPLEX, .54, color, 2, cv2.LINE_AA)


def save_run(samples, prediction, top, bottom):
    result = analyze(samples, prediction)
    OUT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    path = OUT / f"ramp_{stamp}.json"
    graph = OUT / f"ramp_{stamp}.png"
    stored = {k: v for k, v in result.items() if k not in ("time", "position", "velocity")}
    stored.update({
        "lab": "Ramp Physics Lab", "tracker": "OpenCV CSRT",
        "axis_top_px": list(top), "axis_bottom_px": list(bottom),
        "recorded_at_local": datetime.now().isoformat(timespec="seconds"),
        "samples": samples,
        "note": "Speed trend is an approximate image-space estimate, not a force or gravity measurement."
    })
    path.write_text(json.dumps(stored, indent=2), encoding="utf-8")
    fig, axes = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
    axes[0].plot(result["time"], result["position"])
    axes[0].set_ylabel("Along-ramp position (px)")
    axes[0].set_title("PhysiLearn — Ramp Motion")
    axes[1].plot(result["time"], result["velocity"])
    axes[1].set_ylabel("Signed along-ramp velocity (px/s)")
    axes[1].set_xlabel("Time since recording began (s)")
    for ax in axes: ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(graph, dpi=150)
    plt.close(fig)
    print("\n=== RAMP PHYSICS RESULTS ===")
    print("Prediction:", prediction)
    print(f"Duration: {result['duration_s']:.2f} s")
    print(f"Along-ramp displacement: {result['along_ramp_displacement_px']:.1f} px")
    print(f"Approximate along-ramp path: {result['approx_along_ramp_path_px']:.1f} px")
    print("Estimated speed trend:", result["estimated_downhill_speed_trend_px_s2"], "px/s^2")
    print(result["assessment"])
    print("Pixel estimates only; camera/tracking noise may affect the result.")
    print("Saved JSON:", path)
    print("Saved graph:", graph)
    return result


def main():
    print("\nPHYSILEARN — RAMP PHYSICS LAB")
    print("Keep camera fixed and SIDE-ON. Use a short, stable ramp.")
    print("Prediction: Will the car speed up as it rolls DOWN the ramp?")
    choice = input("Choose 1 = speed increases, 2 = stays about the same [1]: ").strip()
    prediction = "Speed stays about the same" if choice == "2" else "Speed increases"
    print("\n3: click TOP then BOTTOM of ramp | 1: select car | 4: record | 5: reset | 2: quit")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Camera not available. Close other camera applications.")
        return
    axis = []
    choose_axis = False
    tracker = None
    recording = False
    samples = []
    start = 0.0
    last_raw = None
    smoothed = None
    notice = "3: mark ramp TOP then BOTTOM"

    def on_mouse(event, x, y, flags, userdata):
        nonlocal choose_axis, tracker, notice, axis
        if choose_axis and event == cv2.EVENT_LBUTTONDOWN:
            axis.append((x, y))
            if len(axis) == 2:
                if math.dist(axis[0], axis[1]) < 30:
                    axis.clear()
                    notice = "Points too close: press 3 and try again"
                else:
                    notice = "Ramp marked. Press 1 to select the car."
                choose_axis = False

    cv2.namedWindow(WINDOW)
    cv2.setMouseCallback(WINDOW, on_mouse)
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("Camera frame unavailable")
                break
            tracked = False
            center = None
            if tracker is not None:
                ok_box, box = tracker.update(frame)
                if ok_box:
                    x, y, w, h = [int(v) for v in box]
                    center = (x + w / 2, y + h / 2)
                    tracked = True
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.circle(frame, (int(center[0]), int(center[1])), 4, (0, 0, 255), -1)
                elif recording:
                    recording = False
                    samples = []
                    notice = "Tracking lost — recording discarded"
                    print(notice)
            if len(axis) == 2:
                cv2.arrowedLine(frame, axis[0], axis[1], (255, 0, 255), 2, tipLength=.05)
                cv2.putText(frame, "TOP", (axis[0][0], axis[0][1] - 8), cv2.FONT_HERSHEY_SIMPLEX, .5, (255, 0, 255), 2)
                cv2.putText(frame, "BOTTOM", (axis[1][0], axis[1][1] - 8), cv2.FONT_HERSHEY_SIMPLEX, .5, (255, 0, 255), 2)
            elif len(axis) == 1:
                cv2.circle(frame, axis[0], 5, (255, 0, 255), -1)
            if recording and tracked and len(axis) == 2:
                now = time.perf_counter()
                if last_raw is not None and math.dist(last_raw, center) > MAX_JUMP_PX:
                    recording = False
                    samples = []
                    notice = "Tracking jumped — recording discarded"
                    print(notice)
                else:
                    last_raw = center
                    if smoothed is None:
                        smoothed = center
                    else:
                        smoothed = (SMOOTH_ALPHA * center[0] + (1-SMOOTH_ALPHA) * smoothed[0],
                                    SMOOTH_ALPHA * center[1] + (1-SMOOTH_ALPHA) * smoothed[1])
                    samples.append({"time_s": round(now - start, 4),
                                    "x_px": round(smoothed[0], 3),
                                    "y_px": round(smoothed[1], 3),
                                    "along_ramp_px": round(project(smoothed, *axis), 3)})
            draw_text(frame, "3: Ramp | 1: Car | 4: Record | 5: Reset | 2: Quit", 28)
            draw_text(frame, "PIXEL MODE — side view, camera fixed", 58, (0, 255, 255))
            if recording:
                draw_text(frame, f"RECORDING {time.perf_counter() - start:.1f}s — press 4 to stop", 90, (0, 0, 255))
            else:
                draw_text(frame, notice, 90, (0, 255, 255))
            cv2.imshow(WINDOW, frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("3"):
                if recording:
                    print("Stop recording before changing ramp")
                    continue
                axis.clear()
                choose_axis = True
                notice = "Click ramp TOP, then BOTTOM"
            elif key == ord("1"):
                if recording:
                    print("Stop recording before selecting car")
                    continue
                roi = cv2.selectROI(WINDOW, frame, fromCenter=False, showCrosshair=True)
                cv2.setMouseCallback(WINDOW, on_mouse)
                if roi[2] and roi[3]:
                    try:
                        tracker = (cv2.TrackerCSRT_create() if hasattr(cv2, "TrackerCSRT_create")
                                   else cv2.legacy.TrackerCSRT_create())
                        tracker.init(frame, roi)
                        notice = "Car selected — press 4 to record"
                    except AttributeError:
                        print("OpenCV CSRT missing. Install opencv-contrib-python in .venv")
                        tracker = None
            elif key == ord("4"):
                if not recording:
                    if len(axis) != 2 or not tracked or choose_axis:
                        print("First mark ramp (3) and select car (1)")
                        continue
                    samples = []
                    start = time.perf_counter()
                    last_raw = None
                    smoothed = None
                    recording = True
                    notice = "Recording started"
                    print("Recording: release the car without pushing; press 4 to stop")
                else:
                    recording = False
                    try:
                        save_run(samples, prediction, *axis)
                        notice = "Saved graphs + JSON to experiments/ramp"
                    except (ValueError, OSError) as ex:
                        notice = f"Not saved: {ex}"
                        print(notice)
            elif key == ord("5"):
                if recording:
                    print("Stop recording first")
                    continue
                tracker = None
                axis.clear()
                choose_axis = False
                notice = "Reset — mark ramp with 3"
            elif key == ord("2"):
                if recording:
                    print("Recording was not saved (press 4 to stop next time)")
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
