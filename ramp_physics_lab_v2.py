"""PhysiLearn Eureka — Ramp Physics Lab v2.

No prediction prompt. Use a fixed side-facing camera and a LOW, stable ramp.
Measurements are in image pixels, not meters; tracking error is possible.

Controls in the camera window:
  3: click ramp TOP then BOTTOM
  1: select / reselect toy car after tracking pause (rectangle; Enter)
  4: start/stop recording
  5: reset tracker and ramp
  2: quit
"""
from __future__ import annotations

import json
import math
import time
from datetime import datetime
from pathlib import Path

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "experiments" / "ramp"
WINDOW = "PhysiLearn | Ramp Physics Lab"
SMOOTH_ALPHA = 0.40
MAX_JUMP_PX = 95  # suspicious movement; pause for re-selection, never discard samples
WINDOW_SECONDS = 0.45


def along_ramp(point, top, bottom):
    """Projection of a 2D point onto the top-to-bottom ramp axis (pixels)."""
    d = np.asarray(bottom, float) - np.asarray(top, float)
    norm = float(np.linalg.norm(d))
    if norm < 30:
        raise ValueError("Ramp markers too close")
    return float(np.dot(np.asarray(point, float) - np.asarray(top, float), d / norm))


def velocity_estimate(t, p):
    """Signed velocity using a centered moving linear regression."""
    out = np.zeros(len(t))
    for i in range(len(t)):
        ids = np.flatnonzero(np.abs(t - t[i]) <= WINDOW_SECONDS / 2)
        if len(ids) < 3:
            continue
        xt = t[ids] - t[ids].mean()
        den = float(xt @ xt)
        if den > 1e-9:
            out[i] = float((xt @ (p[ids] - p[ids].mean())) / den)
    return out


def summarize(samples, tracking_interruptions=0):
    """Summarize validated samples without connecting lost-tracking intervals.

    Time is elapsed real recording time (including tracking gaps), while the
    approximate path only includes consecutive samples from the same segment.
    """
    if len(samples) < 12:
        raise ValueError("Not enough samples; record a little longer")
    absolute_t = np.asarray([s["time_s"] for s in samples], dtype=float)
    p = np.asarray([s["along_ramp_px"] for s in samples], dtype=float)
    segments = np.asarray([s.get("segment_id", 0) for s in samples], dtype=int)
    if (not np.all(np.diff(absolute_t) > 0)) or absolute_t[-1] - absolute_t[0] < 0.7:
        raise ValueError("Recording too short or timestamps invalid")
    t = absolute_t - absolute_t[0]
    p = p - p[0]
    v = np.zeros(len(t))
    observed_time = 0.0
    segments_seen = []
    for seg_id in np.unique(segments):
        ids = np.flatnonzero(segments == seg_id)
        if len(ids) == 0:
            continue
        segments_seen.append(int(seg_id))
        if len(ids) > 1:
            observed_time += float(t[ids[-1]] - t[ids[0]])
        if len(ids) >= 3:
            # Never fit a velocity window across a tracking gap.
            v[ids] = velocity_estimate(t[ids], p[ids])
    consecutive = segments[1:] == segments[:-1]
    tracked_path = float(np.abs(np.diff(p))[consecutive].sum())
    positive_peak = float(max(0.0, np.max(v)))
    threshold = max(15.0, positive_peak * 0.12)
    moving_ids = np.flatnonzero(v > threshold)
    moving_duration = None
    if len(moving_ids) >= 3:
        # Sum moving durations inside each continuous tracking segment, never
        # span from before an occlusion to after re-acquiring the car.
        dt = np.diff(t)
        moving_steps = (v[:-1] > threshold) & (v[1:] > threshold) & consecutive
        moving_duration = float(dt[moving_steps].sum())
    gaps = max(0, len(segments_seen) - 1, tracking_interruptions)
    return {
        "duration_s": round(float(t[-1]), 3),
        "along_ramp_displacement_px": round(float(p[-1]), 2),
        "approx_along_ramp_path_px": round(tracked_path, 2),
        "peak_downhill_velocity_px_s": round(positive_peak, 2),
        "approx_motion_duration_s": None if moving_duration is None else round(moving_duration, 2),
        "tracking_gaps": gaps,
        "observed_tracking_duration_s": round(observed_time, 3),
        "path_complete": gaps == 0,
        "units": "pixels (image-space, uncalibrated)",
        "t": t,
        "p": p,
        "v": v,
        "segments": segments,
    }


def save_experiment(samples, top, bottom, tracking_interruptions=0):
    result = summarize(samples, tracking_interruptions)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    json_path = OUTPUT / f"ramp_v2_{stamp}.json"
    graph_path = OUTPUT / f"ramp_v2_{stamp}.png"
    stored = {k: v for k, v in result.items() if k not in ("t", "p", "v", "segments")}
    note = ("Tracking was interrupted; only observed segments were summed for path. "
            "Displacement spans first and last observations and may include unobserved travel. "
            "Do not interpret path/displacement ratios or cross-gap velocity as reliable. "
            if result["tracking_gaps"] else "")
    note += "Pixel measurements are approximate. Peak velocity may be affected by tracker noise."
    stored.update({
        "lab": "Ramp Physics Lab v2",
        "tracker": "OpenCV CSRT",
        "axis_top_px": list(top),
        "axis_bottom_px": list(bottom),
        "samples": samples,
        "note": note,
    })
    json_path.write_text(json.dumps(stored, indent=2), encoding="utf-8")

    fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    for j, seg in enumerate(np.unique(result["segments"])):
        inds = np.flatnonzero(result["segments"] == seg)
        if len(inds) < 2:
            continue
        axes[0].plot(result["t"][inds], result["p"][inds],
                     label="Tracked segment" if j == 0 else None)
        axes[1].plot(result["t"][inds], result["v"][inds])
    axes[0].set_ylabel("Position along ramp (px)")
    axes[0].set_title("PhysiLearn | Ramp Physics Experiment")
    axes[1].axhline(0, linewidth=0.8, linestyle="--")
    axes[1].set_ylabel("Estimated velocity (px/s)")
    axes[1].set_xlabel("Time (seconds)")
    for ax in axes:
        ax.grid(alpha=0.25)
    if result["tracking_gaps"]:
        fig.text(.5, .01, "Tracking gaps: missing movement is NOT interpolated",
                 ha="center", fontsize=9)
        fig.tight_layout(rect=(0, .035, 1, 1))
    else:
        fig.tight_layout()
    fig.savefig(graph_path, dpi=150)
    plt.close(fig)

    print("\n===== RAMP PHYSICS RESULTS =====")
    print(f"Recording time:       {result['duration_s']:.2f} s")
    print(f"Displacement:         {result['along_ramp_displacement_px']:.1f} px")
    print(f"Observed path:        {result['approx_along_ramp_path_px']:.1f} px")
    print(f"Peak downhill speed:  {result['peak_downhill_velocity_px_s']:.1f} px/s")
    if result["approx_motion_duration_s"] is not None:
        print(f"Approx. moving time:  {result['approx_motion_duration_s']:.2f} s")
    if result["tracking_gaps"]:
        print(f"WARNING: {result['tracking_gaps']} tracking gap(s); path incomplete.")
    print("These are image-space estimates, not real-world speed or acceleration.")
    print("Graph:", graph_path)
    print("Data: ", json_path)
    return result


def overlay(frame, status, status_color, details, results=None):
    """Draw a clear, translucent HUD without hiding most of the camera view."""
    h, w = frame.shape[:2]
    hud_h = 118 if results is None else 175
    hud_h = min(hud_h, h)
    dark = frame.copy()
    cv2.rectangle(dark, (0, 0), (w, hud_h), (28, 30, 37), -1)
    cv2.addWeighted(dark, 0.83, frame, 0.17, 0, frame)
    cv2.putText(frame, "PHYSILEARN  |  RAMP LAB", (14, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(frame, "1: Select   2: Exit   3: Ramp   4: Record   5: Reset", (14, 49),
                cv2.FONT_HERSHEY_SIMPLEX, 0.47, (205, 211, 218), 1, cv2.LINE_AA)
    cv2.putText(frame, status[:70], (14, 78),
                cv2.FONT_HERSHEY_SIMPLEX, 0.57, status_color, 2, cv2.LINE_AA)
    cv2.putText(frame, details[:82], (14, 104),
                cv2.FONT_HERSHEY_SIMPLEX, 0.46, (220, 225, 232), 1, cv2.LINE_AA)
    if results is not None:
        line1 = f"Time: {results['duration_s']:.2f}s    Path: {results['approx_along_ramp_path_px']:.0f}px"
        line2 = f"Displacement: {results['along_ramp_displacement_px']:.0f}px    Peak: {results['peak_downhill_velocity_px_s']:.0f}px/s"
        cv2.putText(frame, line1, (14, 137), cv2.FONT_HERSHEY_SIMPLEX, .54,
                    (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frame, line2, (14, 160), cv2.FONT_HERSHEY_SIMPLEX, .48,
                    (255, 255, 255), 1, cv2.LINE_AA)


def run():
    # PHYSILEARN_RAMP_RECOVERY_V1
    # PHYSILEARN_RAMP_MATCH_OBJECT_CAMERA_V2
    # These settings match the already working Object Physics Lab.
    # MJPG + DirectShow often allow higher-resolution live capture on Windows.
    cap = (cv2.VideoCapture(0, cv2.CAP_DSHOW)
           if hasattr(cv2, "CAP_DSHOW") else cv2.VideoCapture(0))
    if not cap.isOpened():
        cap.release()
        cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Cannot access webcam; close other camera programs")
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    # OpenCV/Windows may negotiate a different mode; log the actual dimensions.
    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Ramp camera: {actual_w}x{actual_h} (requested 1280x720)")
    markers = []
    marking = False
    tracker = None
    recording = False
    paused_tracking = False
    samples = []
    start = None
    smooth = None
    last_raw = None
    current_segment = 0
    interruptions = 0
    result = None
    mirror_correction = True  # M toggles this if the webcam was already unmirrored.
    fullscreen_view = True    # F switches between fullscreen and windowed display.
    status = "Ready - first press 3 to mark your ramp"
    print("Ramp Lab: 3 ramp | 1 car/reselect | 4 record/finish | 5 reset | 2 quit")

    def mouse(event, x, y, flags, userdata):
        nonlocal marking, status, result
        if marking and event == cv2.EVENT_LBUTTONDOWN:
            markers.append((x, y))
            if len(markers) == 2:
                if math.dist(*markers) < 30:
                    markers.clear()
                    status = "Markers too close - press 3 again"
                else:
                    status = "Ramp marked - select the car with 1"
                marking = False

    # Same full-screen preview behavior as Object Physics Lab.
    # KEEPRATIO prevents distorting the tracked motion.
    cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
    try:
        cv2.setWindowProperty(WINDOW, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    except cv2.error:
        cv2.resizeWindow(WINDOW, 1200, 800)
    cv2.setMouseCallback(WINDOW, mouse)
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("No webcam image")
                break
            # Correct a webcam's mirrored preview BEFORE tracking / selecting / marking.
            # All annotations, ROI and physical coordinates use the same orientation.
            if mirror_correction:
                frame = cv2.flip(frame, 1)
            tracked, center = False, None
            if tracker is not None and not paused_tracking:
                found, box = tracker.update(frame)
                if found:
                    x, y, width, height = map(int, box)
                    center = (x + width / 2, y + height / 2)
                    tracked = True
                    cv2.rectangle(frame, (x, y), (x + width, y + height), (80, 220, 110), 2)
                    cv2.circle(frame, tuple(map(int, center)), 4, (40, 90, 245), -1)
                elif recording:
                    paused_tracking = True
                    interruptions += 1
                    tracker = None
                    last_raw, smooth = None, None
                    status = "Tracking lost - PAUSED. Press 1 to reselect, 4 to save"
                    print(status)
            if len(markers) == 2:
                cv2.arrowedLine(frame, markers[0], markers[1], (220, 80, 220), 2, tipLength=0.06)
                cv2.putText(frame, "TOP", (markers[0][0], max(15, markers[0][1] - 8)),
                            cv2.FONT_HERSHEY_SIMPLEX, .52, (220, 80, 220), 2)
                cv2.putText(frame, "BOTTOM", (markers[1][0], max(15, markers[1][1] - 8)),
                            cv2.FONT_HERSHEY_SIMPLEX, .52, (220, 80, 220), 2)
            elif len(markers) == 1:
                cv2.circle(frame, markers[0], 5, (220, 80, 220), -1)

            if recording and tracked and not paused_tracking:
                now = time.perf_counter()
                # An extreme jump is more likely a tracker switch/occlusion.
                # Pause instead of wiping all the previous recording.
                if last_raw is not None and math.dist(last_raw, center) > MAX_JUMP_PX:
                    paused_tracking = True
                    interruptions += 1
                    tracker = None
                    last_raw, smooth = None, None
                    status = "Tracker jumped - PAUSED. Press 1 to reselect, 4 to save"
                    print(status)
                else:
                    last_raw = center
                    if smooth is None:
                        smooth = center
                    else:
                        smooth = (SMOOTH_ALPHA * center[0] + (1-SMOOTH_ALPHA) * smooth[0],
                                  SMOOTH_ALPHA * center[1] + (1-SMOOTH_ALPHA) * smooth[1])
                    samples.append({
                        "time_s": round(now-start, 4),
                        "x_px": round(smooth[0], 3),
                        "y_px": round(smooth[1], 3),
                        "along_ramp_px": round(along_ramp(smooth, *markers), 3),
                        "segment_id": current_segment,
                    })
            if recording and paused_tracking:
                label = "TRACKING PAUSED - 1: Reselect car   4: Save partial"
                color = (0, 180, 255)
            elif recording:
                label = f"RECORDING {time.perf_counter() - start:.1f}s - press 4 to finish"
                color = (100, 130, 255)
            else:
                label = status
                color = (125, 235, 185)
            details = "Pixels only | M: Flip image | F: Fullscreen | Keep camera fixed"
            overlay(frame, label, color, details, results=result if not recording else None)
            cv2.imshow(WINDOW, frame)
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("m"), ord("M")):
                if recording:
                    status = "Finish recording (4) before flipping the camera"
                    print(status)
                else:
                    mirror_correction = not mirror_correction
                    # Reversing x changes all click/ROI coordinates. Require a fresh setup.
                    tracker = None
                    markers.clear()
                    marking = False
                    paused_tracking = False
                    smooth, last_raw = None, None
                    result = None
                    status = "Image flipped - press 3 to mark ramp, then 1 to select car"
                    print(status)
            elif key in (ord("f"), ord("F")):
                fullscreen_view = not fullscreen_view
                cv2.setWindowProperty(
                    WINDOW, cv2.WND_PROP_FULLSCREEN,
                    cv2.WINDOW_FULLSCREEN if fullscreen_view else cv2.WINDOW_NORMAL,
                )
                if not fullscreen_view:
                    cv2.resizeWindow(WINDOW, 1080, 680)
            elif key == ord("3") and not recording:
                markers.clear()
                marking = True
                result = None
                status = "Click ramp TOP then BOTTOM"
            elif key == ord("1") and (not recording or paused_tracking):
                roi = cv2.selectROI(WINDOW, frame, fromCenter=False, showCrosshair=True)
                cv2.setMouseCallback(WINDOW, mouse)
                if roi[2] > 0 and roi[3] > 0:
                    tracker = (cv2.TrackerCSRT_create() if hasattr(cv2, "TrackerCSRT_create")
                               else cv2.legacy.TrackerCSRT_create())
                    tracker.init(frame, roi)
                    if recording and paused_tracking:
                        # Start a new independent segment, with no fake travel
                        # between the last and newly acquired locations.
                        current_segment += 1
                        last_raw, smooth = None, None
                        paused_tracking = False
                        status = "Tracking resumed - missing span marked"
                    else:
                        status = "Car selected - press 4 to record"
                        result = None
            elif key == ord("4"):
                if not recording:
                    if marking or len(markers) != 2 or not tracked:
                        status = "Mark ramp (3), select car (1), then record (4)"
                        print(status)
                        continue
                    samples, smooth, last_raw = [], None, None
                    current_segment = 0
                    interruptions = 0
                    paused_tracking = False
                    start = time.perf_counter()
                    recording = True
                    result = None
                    print("Recording started; release car, press 4 to stop")
                else:
                    recording = False
                    paused_tracking = False
                    try:
                        result = save_experiment(samples, *markers, tracking_interruptions=interruptions)
                        status = ("Experiment saved (incomplete tracking) - see experiments/ramp"
                                  if result["tracking_gaps"] else
                                  "Experiment saved - see experiments/ramp")
                    except (ValueError, OSError) as ex:
                        result = None
                        status = "Cannot save - check terminal"
                        print(f"Experiment invalid: {ex}")
            elif key == ord("5") and not recording:
                tracker, markers, result = None, [], None
                marking = False
                paused_tracking = False
                status = "Reset - press 3 to mark ramp"
            elif key == ord("2"):
                if recording:
                    print("Recording not saved; stop with 4 before exiting")
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    run()
