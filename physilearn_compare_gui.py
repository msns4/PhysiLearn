"""PhysiLearn: graphical comparison of saved Object Lab recordings.

Launched from app_eureka.py. Does not open a console or edit source experiments.
Uses existing, tested read_experiment() and get_plot_series() calculations.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import math

import customtkinter as ctk
from PIL import Image

from compare_experiments import read_experiment, get_plot_series

BASE = Path(__file__).resolve().parent
EXPERIMENTS = BASE / "experiments"
COMPARISONS = BASE / "comparisons"


class ComparisonWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("PhysiLearn | Compare Experiments")
        self.geometry("1160x840")
        self.minsize(960, 720)
        self.configure(fg_color="#202020")
        self._window_image = None
        self._records = {}
        self._by_unit = {"cm": [], "px": []}
        self._unit = "cm"
        self._chart_path = None
        self.after(200, self.lift)
        self._draw()
        self._load_records()

    def _label(self, text, parent, size=13, weight="normal", color=None, **kwargs):
        return ctk.CTkLabel(parent, text=text,
                            font=ctk.CTkFont(size=size, weight=weight),
                            text_color=color, **kwargs)

    def _draw(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=30, pady=(20, 4))
        self._label("Compare Experiments", top, 29, "bold").pack(anchor="w")
        self._label("Compare two saved Object Lab recordings without using the terminal.",
                    top, 13, color="#c5cbd5").pack(anchor="w", pady=(0, 11))

        controls = ctk.CTkFrame(self, corner_radius=15)
        controls.pack(fill="x", padx=30, pady=(0, 10))
        row = ctk.CTkFrame(controls, fg_color="transparent")
        row.pack(fill="x", padx=15, pady=(13, 8))
        self._label("Units", row, 13, "bold").pack(side="left", padx=(0, 12))
        self.unit_toggle = ctk.CTkSegmentedButton(
            row, values=["cm", "px"], command=self._change_unit, width=150)
        self.unit_toggle.pack(side="left")
        ctk.CTkButton(row, text="Refresh recordings", width=150,
                      fg_color="#3a4657", hover_color="#4b5b72",
                      command=self._load_records).pack(side="right")

        picks = ctk.CTkFrame(controls, fg_color="transparent")
        picks.pack(fill="x", padx=15, pady=(0, 13))
        picks.grid_columnconfigure((0, 1), weight=1, uniform="rec")
        for col, name in ((0, "EXPERIMENT A"), (1, "EXPERIMENT B")):
            self._label(name, picks, 12, "bold", "#80bbf2").grid(
                row=0, column=col, padx=(0 if col == 0 else 10, 10), sticky="w")
        self.combo_a = ctk.CTkComboBox(picks, values=["No recordings"],
                                      state="readonly", width=430, height=38)
        self.combo_b = ctk.CTkComboBox(picks, values=["No recordings"],
                                      state="readonly", width=430, height=38)
        self.combo_a.grid(row=1, column=0, padx=(0, 10), pady=(7, 0), sticky="ew")
        self.combo_b.grid(row=1, column=1, padx=(10, 0), pady=(7, 0), sticky="ew")

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", padx=30, pady=(0, 7))
        self.compare_button = ctk.CTkButton(actions, text="Compare Selected Runs  →",
                                             height=42, width=250,
                                             font=ctk.CTkFont(size=14, weight="bold"),
                                             command=self._compare)
        self.compare_button.pack(side="left")
        self.status = self._label("Choose two recordings to compare.", actions, 12,
                                  color="#bfc7d1", wraplength=780, justify="left")
        self.status.pack(side="left", padx=17)

        metrics = ctk.CTkFrame(self, corner_radius=15)
        metrics.pack(fill="x", padx=30, pady=(0, 9))
        metrics.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="metric")
        self.metrics = {}
        definitions = (("Distance", "distance"), ("Displacement", "displacement_magnitude"),
                       ("Time", "duration_s"), ("Average speed", "average_speed"))
        for idx, (title, key) in enumerate(definitions):
            frame = ctk.CTkFrame(metrics, fg_color="#323437", corner_radius=10)
            frame.grid(row=0, column=idx, sticky="ew", padx=7, pady=10)
            self._label(title.upper(), frame, 11, "bold", "#b7c4d0").pack(pady=(9, 2))
            values = self._label("A —    |    B —", frame, 14, "bold", "#a2d3ff")
            values.pack(pady=(0, 11))
            self.metrics[key] = values

        graph_header = ctk.CTkFrame(self, fg_color="transparent")
        graph_header.pack(fill="x", padx=30, pady=(2, 5))
        self._label("Motion Graphs", graph_header, 18, "bold").pack(side="left")
        self._label("Position and estimated speed versus time", graph_header, 12,
                    color="#bfc7d1").pack(side="right")
        graph_container = ctk.CTkFrame(self, fg_color="#303030", corner_radius=15)
        graph_container.pack(fill="both", expand=True, padx=30, pady=(0, 9))
        self.chart = ctk.CTkLabel(graph_container, text="Choose two runs and click Compare.",
                                  font=ctk.CTkFont(size=15), text_color="#c9ced7")
        self.chart.pack(expand=True, fill="both", padx=10, pady=9)
        self.note = self._label(
            "Only compatible units can be compared. Results are descriptive, not proof of a cause.",
            self, 12, color="#c5cbd5", wraplength=1000, justify="center")
        self.note.pack(pady=(0, 15))

    @staticmethod
    def _display_name(path, data):
        parts = path.stem.split("_")
        try:
            stamp = datetime.strptime("_".join(parts[:2]), "%Y%m%d_%H%M%S")
            date = stamp.strftime("%b %d %H:%M")
        except ValueError:
            date = path.stem[:16]
        return f"{date}  ·  {data['object_name']}  ·  {float(data['duration_s']):.2f} s  ·  {data['measurement_units']}  ·  #{parts[2] if len(parts) > 2 else path.stem[-6:]}"

    def _load_records(self):
        self._records.clear()
        self._by_unit = {"cm": [], "px": []}
        errors = 0
        for path in sorted(EXPERIMENTS.glob("*.json"), reverse=True):
            try:
                data = read_experiment(path)
                unit = data["measurement_units"]
                label = self._display_name(path, data)
                self._records[label] = (path, data)
                self._by_unit[unit].append(label)
            except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError):
                errors += 1
        # Select the meaningful default; cm if at least two valid calibrated runs exist.
        if len(self._by_unit["cm"]) >= 2:
            target = "cm"
        elif len(self._by_unit["px"]) >= 2:
            target = "px"
        else:
            target = "cm"
        self.unit_toggle.set(target)
        self._change_unit(target)
        total = len(self._records)
        self.status.configure(text=f"Found {total} valid recordings" +
                              (f" · Skipped {errors} unreadable files" if errors else ""),
                              text_color="#c5cbd5")

    def _change_unit(self, unit):
        self._unit = unit
        values = self._by_unit[unit]
        choices = values if values else ["No recordings in " + unit]
        for combo in (self.combo_a, self.combo_b):
            combo.configure(values=choices)
        self.combo_a.set(choices[0])
        self.combo_b.set(choices[1] if len(values) > 1 else choices[0])
        self.compare_button.configure(state="normal" if len(values) >= 2 else "disabled")
        if len(values) < 2:
            self.status.configure(text=f"Need at least two Object Lab recordings in {unit}.",
                                  text_color="#ffd18d")
        else:
            self.status.configure(text=f"Choose any two different {unit} recordings.",
                                  text_color="#c5cbd5")

    def _compare(self):
        label_a, label_b = self.combo_a.get(), self.combo_b.get()
        if label_a == label_b:
            self.status.configure(text="Choose TWO different recordings.",
                                  text_color="#ffce93")
            return
        if label_a not in self._records or label_b not in self._records:
            self.status.configure(text="Invalid selection. Click Refresh recordings.",
                                  text_color="#ffce93")
            return
        a_path, a = self._records[label_a]
        b_path, b = self._records[label_b]
        unit = a["measurement_units"]
        if b["measurement_units"] != unit:
            self.status.configure(text="Cannot compare cm against px. Choose matching units.",
                                  text_color="#ffce93")
            return
        try:
            for key in self.metrics:
                av, bv = float(a[key]), float(b[key])
                if not (math.isfinite(av) and math.isfinite(bv)):
                    raise ValueError("Recording contains invalid numerical data")
                suffix = " s" if key == "duration_s" else (f" {unit}/s" if key == "average_speed" else f" {unit}")
                self.metrics[key].configure(text=f"A {av:.2f}{suffix}  |  B {bv:.2f}{suffix}")
            png = self._create_comparison_plot(a, b, unit)
            with Image.open(png) as im:
                img = im.convert("RGB").copy()
            self._window_image = ctk.CTkImage(light_image=img, dark_image=img,
                                              size=(930, 370))
            self.chart.configure(image=self._window_image, text="")
            self._chart_path = png
            self.status.configure(text="Comparison ready · Graph saved in comparisons/",
                                  text_color="#9de4bd")
            self.note.configure(text=(
                "Calibrated cm: only compare meaningfully when both measurements used accurate calibration "
                "and compatible camera geometry. Different surfaces or pushes do not prove causation."
                if unit == "cm" else
                "Pixel mode: image-space values only. Use matching camera setup and depth; "
                "do not interpret px or px/s as physical units."))
        except Exception as exc:
            # Do not disclose secrets or excessive system information in the UI.
            self.status.configure(text=f"Could not compare recordings: {type(exc).__name__}.",
                                  text_color="#ffce93")
            print("Compare Experiments GUI error:", type(exc).__name__)

    @staticmethod
    def _create_comparison_plot(a, b, unit):
        import matplotlib
        matplotlib.use("Agg")
        from matplotlib import pyplot as plt
        t_a, x_a, v_a = get_plot_series(a)
        t_b, x_b, v_b = get_plot_series(b)
        figure, axes = plt.subplots(2, 1, figsize=(10.2, 4.1), dpi=125)
        for name, ts, x, speed in (("A: " + a["object_name"], t_a, x_a, v_a),
                                   ("B: " + b["object_name"], t_b, x_b, v_b)):
            axes[0].plot(ts, x, label=name, linewidth=1.9)
            axes[1].plot(ts, speed, label=name, linewidth=1.9)
        axes[0].set_ylabel("Horizontal position (" + unit + ")")
        axes[1].set_ylabel("Estimated speed (" + unit + "/s)")
        axes[1].set_xlabel("Time (s)")
        for axis in axes:
            axis.grid(alpha=0.3)
            axis.legend(loc="upper right", fontsize=8)
            axis.set_xlim(left=0)
        figure.tight_layout(pad=1.1)
        COMPARISONS.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        png = COMPARISONS / f"comparison_{stamp}.png"
        try:
            figure.savefig(png, dpi=125, facecolor="white")
        finally:
            plt.close(figure)
        return png


def open_comparison_window(parent):
    """Open a CTk window from PhysiLearn main page; never spawn a terminal."""
    try:
        ComparisonWindow(parent)
    except Exception as exc:
        print("Unable to open comparison window:", type(exc).__name__)
        raise
