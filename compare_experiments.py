r"""PhysiLearn 2.0 — Compare Experiments.

Reads the individual JSON files written by object_physics_lab_v2.py.
Compares two runs without modifying either original recording.

Run:
    .\.venv\Scripts\python.exe compare_experiments.py

Pixel measurements are image-space estimates, not physical units.
Only compare physical results when calibration and camera setup are appropriate.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_DIR = Path(__file__).resolve().parent
EXPERIMENTS_DIR = PROJECT_DIR / "experiments"
COMPARISONS_DIR = PROJECT_DIR / "comparisons"


def read_experiment(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    mandatory = (
        "object_name", "measurement_units", "distance", "displacement_magnitude",
        "duration_s", "average_speed", "samples",
    )
    missing = [key for key in mandatory if key not in data]
    if missing:
        raise ValueError(f"{path.name}: missing fields: {', '.join(missing)}")
    if data["measurement_units"] not in ("cm", "px"):
        raise ValueError(f"{path.name}: unsupported units")
    if not isinstance(data["samples"], list) or len(data["samples"]) < 2:
        raise ValueError(f"{path.name}: not enough samples")
    if data["measurement_units"] == "cm" and not data.get("pixels_per_cm"):
        raise ValueError(f"{path.name}: cm results require a valid calibration value")
    return data


def get_plot_series(data: dict) -> tuple[list[float], list[float], list[float]]:
    samples = data["samples"]
    scale = float(data["pixels_per_cm"]) if data["measurement_units"] == "cm" else 1.0
    t0 = float(samples[0]["time_s"])
    x0 = float(samples[0]["x_px"])
    times = [float(s["time_s"]) - t0 for s in samples]
    positions = [(float(s["x_px"]) - x0) / scale for s in samples]

    # Average travel speed in a rolling 0.4-second window.
    # The source's cumulative-distance field already applies its tracking filter.
    speeds = [0.0] * len(samples)
    j = 0
    window = float(data.get("speed_estimate_window_s", 0.4))
    for i in range(1, len(samples)):
        while j < i - 1 and times[i] - times[j + 1] >= window:
            j += 1
        dt = times[i] - times[j]
        delta = (
            float(samples[i]["cumulative_distance_px"])
            - float(samples[j]["cumulative_distance_px"])
        )
        speeds[i] = max(0.0, delta / dt / scale) if dt > 1e-6 else 0.0
    return times, positions, speeds


def choose_pair(files: list[Path]) -> tuple[Path, Path] | None:
    """Keep asking until two readable runs with matching units are selected.

    Returns None when the user wants to leave comparison mode.
    """
    print("\nAvailable recordings:")
    for idx, path in enumerate(files, start=1):
        try:
            data = read_experiment(path)
            desc = f"{data['object_name']} | {data['duration_s']:.2f} s | {data['measurement_units']}"
        except (ValueError, OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
            desc = f"could not read: {exc}"
        print(f"  {idx}. {path.name}  ({desc})")

    while True:
        print("\nEnter two run numbers, e.g. 3 21.")
        print("Enter = use two newest runs | Q = back/quit")
        try:
            selection = input("Choose two recordings: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting comparison.")
            return None
        if selection.lower() in ("q", "quit", "exit"):
            return None
        if not selection:
            a_idx, b_idx = len(files) - 2, len(files) - 1
        else:
            values = selection.replace(",", " ").split()
            if len(values) != 2 or not all(v.isdecimal() for v in values):
                print("Please enter exactly two numbers separated by a space (e.g. 3 21).")
                continue
            a_idx, b_idx = (int(v) - 1 for v in values)
        if a_idx == b_idx or not (0 <= a_idx < len(files)) or not (0 <= b_idx < len(files)):
            print(f"Please choose two DIFFERENT numbers from 1 to {len(files)}.")
            continue
        a_path, b_path = files[a_idx], files[b_idx]
        try:
            a = read_experiment(a_path)
            b = read_experiment(b_path)
        except (ValueError, OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
            print(f"Cannot use those recordings: {exc}")
            print("You can select another pair without restarting.")
            continue
        if a["measurement_units"] != b["measurement_units"]:
            print(f"Different units: #{a_idx + 1} is {a['measurement_units']}, "
                  f"but #{b_idx + 1} is {b['measurement_units']}.")
            print("Choose TWO cm runs or TWO px runs. Nothing was deleted; please try again.")
            continue
        return a_path, b_path


def ask_again() -> bool:
    """Return True if the user wants another comparison."""
    while True:
        try:
            selection = input("\nCompare another pair? [Y/n]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting comparison.")
            return False
        if selection in ("", "y", "yes"):
            return True
        if selection in ("n", "no", "q", "quit", "exit"):
            return False
        print("Please type Y or N.")


def compare_pair(a_path: Path, b_path: Path) -> None:
    """Print and plot one validated compatible pair."""
    a = read_experiment(a_path)
    b = read_experiment(b_path)
    unit = a["measurement_units"]
    if unit != b["measurement_units"]:
        raise ValueError("Recorded units are different; please choose two compatible runs")
    print("\n=== PHYSILEARN: EXPERIMENT COMPARISON ===")
    print(f"Experiment A: {a['object_name']} | {a_path.name}")
    print(f"Experiment B: {b['object_name']} | {b_path.name}")
    print(f"{'Metric':<24} {'A':>12} {'B':>12}")
    print("-" * 50)
    metrics = [
        ("Distance", "distance", unit),
        ("Displacement", "displacement_magnitude", unit),
        ("Duration", "duration_s", "s"),
        ("Average speed", "average_speed", unit + "/s"),
    ]
    for label, key, suffix in metrics:
        print(f"{label:<24} {a[key]:>9.2f} {suffix:<2} {b[key]:>9.2f} {suffix}")

    print("\nNote: distance is total traveled path; displacement is start-to-end separation.")
    print("This is descriptive comparison, not a controlled test of an object's properties.")
    if unit == "px":
        print("PIXEL MODE: camera image units; comparison requires the same camera geometry")
        print("and similar depth, and does not give real cm or cm/s values.")
    else:
        print("CM MODE: valid only with accurately calibrated, fixed camera geometry")
        print("and both objects moving in the same plane as the ruler.")

    t_a, x_a, v_a = get_plot_series(a)
    t_b, x_b, v_b = get_plot_series(b)
    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=False)
    for label, time_, position, speed in [
        ("A: " + a["object_name"], t_a, x_a, v_a),
        ("B: " + b["object_name"], t_b, x_b, v_b),
    ]:
        axes[0].plot(time_, position, label=label, linewidth=1.8)
        axes[1].plot(time_, speed, label=label, linewidth=1.8)
    axes[0].set_title("Position relative to each run's starting point")
    axes[0].set_ylabel(f"Horizontal position ({unit})")
    axes[1].set_title("Estimated speed")
    axes[1].set_ylabel(f"Speed ({unit}/s)")
    axes[1].set_xlabel("Time since recording started (s)")
    for ax in axes:
        ax.grid(alpha=0.3)
        ax.legend()
        ax.set_xlim(left=0)
    fig.suptitle("PhysiLearn — Compare Experiments", fontsize=14)
    fig.tight_layout()

    COMPARISONS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output = COMPARISONS_DIR / f"comparison_{stamp}.png"
    fig.savefig(output, dpi=150)
    plt.close(fig)
    print(f"\nSaved comparison graph: {output}")


def main() -> None:
    while True:
        files = sorted(EXPERIMENTS_DIR.glob("*.json"))
        if len(files) < 2:
            print("Please record at least two runs using Object Physics Lab first.")
            return
        pair = choose_pair(files)
        if pair is None:
            print("Comparison closed. Your recorded experiments were not changed.")
            return
        try:
            compare_pair(*pair)
        except (ValueError, OSError, json.JSONDecodeError, KeyError, TypeError, ZeroDivisionError) as exc:
            print(f"\nCannot compare those recordings: {exc}")
            print("You may select other recordings. No experiment was deleted.")
        if not ask_again():
            print("Comparison closed. Saved charts remain in the comparisons folder.")
            return


if __name__ == "__main__":
    main()
