# PhysiLearn — Webcam Physics Lab

**Turn everyday objects into physics experiments.**

PhysiLearn is a desktop learning prototype that uses a webcam to measure motion, plots the recorded data, applies deterministic physics calculations, and offers an optional AI explanation grounded in the measurements. It is intended for hands-on physics exploration, not laboratory-grade metrology.

## EurekaDev update (October 2026)

This repository originally hosted **PhysiLearn for ForgeHacks 2026** (Tennis Ball Physics and Constant Velocity Hand Challenge). This later **EurekaDev iteration** adds Object Physics Lab, Ramp Physics Lab, measurement calibration, comparisons of saved runs, and AI Motion Insight. The earlier work is acknowledged and preserved in the source.

### Main features

- **Object Physics Lab** — track a toy car, box, tennis ball, or another selected object; record distance, displacement, elapsed time, average speed and motion graphs. Optional ruler calibration makes `cm` and `cm/s` estimates available; otherwise values remain `px` and `px/s`.
- **Ramp Physics Lab** — mark the slope direction, track a car down an incline, examine along-ramp displacement, speed estimates and plots. Values are currently in pixels unless otherwise supported by the implementation.
- **AI Motion Insight** — four short explanations: **How It Moved**, **Why It Changed**, **Physics Behind It**, and **What We Learned**. The optional OpenAI API is used for narrative explanations only, not motion measurement or physics calculations. When AI is unavailable, the built-in local explanation is used.
- **Motion Analysis, Formula Explorer and Physics Principle** — estimated motion intervals, path-vs-displacement concepts, average speed, and contextual physics laws. Uncertainty and possible tracking gaps are reported.
- **Compare Experiments** — choose two saved Object Lab runs using a graphical interface; compare numerical results and plots in compatible units. The viewer keeps `px` and `cm` recordings separate.
- **Classic Labs** — the original tennis-ball experiment and hand-motion challenge remain accessible for reference.

## How it works

```text
Webcam → OpenCV tracking → timestamped positions → Python physics calculations
    → saved JSON + motion graphs → local explanation / optional OpenAI explanation
    → compare calibrated or pixel-based recordings
```

Computer vision estimates positions. Python computes the metrics. The AI explains the results and should not be treated as a source of new measurements.

## Getting started

Recommended: **Windows 10/11, Python 3.12, a webcam**, and an ordinary object to track.

```powershell
git clone https://github.com/msns4/PhysiLearn.git
cd PhysiLearn
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app_eureka.py
```

**Launch `app_eureka.py` for the EurekaDev version.** Running `app.py` instead opens the older ForgeHacks interface.

The legacy Hand Challenge needs `hand_landmarker.task` from the repository root. Other images used by the older interface are under `assets/`.

### Optional OpenAI tutor

The application can work without a cloud AI account. To enable the optional narrative tutor, create a local `.env` file (not committed to Git):

```dotenv
OPENAI_API_KEY=your_own_api_key
PHYSILEARN_AI_MODEL=gpt-4o-mini
```

Use an account with access to the OpenAI API and a sufficient API balance. API usage may incur charges. Do **not** put secret keys in source code, screenshots, issues, or commits. A no-key configuration continues using the local physics explanation.

### Object Lab (with or without ruler)

1. Launch Object Physics Lab and select an object.
2. In the camera window, press `3` to calibrate against the **0 cm and 25 cm** marks of a real 25 cm ruler, kept on the same plane as the object. Or use pixel mode (`5`) without a ruler.
3. Press `1` to select the object, then `4` to start and stop recording. Press `2` to exit/review.
4. Review the graphs and click **Explain with AI** to view the optional interpretation, Motion Analysis, Formula Explorer and Physics Principle.

### Ramp Lab

1. Prepare a low, stable incline with the toy car visible throughout its motion.
2. In Ramp Lab, press `3` to mark the direction of the slope, `1` to select the car and `4` to start/stop recording.
3. Press `2` to leave the camera and review the saved results.
4. The viewer supports `M` to toggle mirrored display and `F` for display mode. After flipping, remark the ramp and object.

### Compare Experiments

Open **Compare Experiments**, choose compatible `cm` or `px` recordings A and B, and click **Compare Selected Runs**. This shows distance, displacement, time, average speed and comparison graphs. It is a descriptive comparison: differing results do not prove what caused them.

## Technology

Python, OpenCV (`opencv-contrib-python`, including object trackers), CustomTkinter, NumPy, Matplotlib, Pillow, optional OpenAI API and python-dotenv. The classic Hand Challenge additionally uses MediaPipe.

## Accuracy and responsible interpretation

- Pixel distances are **not** centimeters. A real ruler in the same plane is needed for approximate centimeters; camera perspective, object height, lighting and tracking noise affect accuracy.
- Occlusions, tracker jumps, and missing segments can underestimate path length or distort peak speed; results may warn about incomplete measurements.
- Average speed uses total tracked path / elapsed time. Displacement is the straight-line separation between start and finish; returning toward the start may reduce displacement but does not by itself reduce average speed.
- The project does not directly measure mass, force, or reliable SI acceleration; physics laws are presented as **conceptual explanations** rather than measured force estimates.
- Physics Tutor may propose physical mechanisms such as friction or pushing, but those causes are hypotheses unless experimentally controlled and tested.
- For fairness, comparisons in different units are intentionally disallowed.

## Repository structure

```text
app_eureka.py                # EurekaDev desktop entry point
object_physics_lab_v2.py     # Object motion tracking and calibration
ramp_physics_lab_v2.py       # Ramp motion tracking
physilearn_compare_gui.py   # Graphical experiment comparison
compare_experiments.py      # Comparison calculations and plotting
eureka_motion_analysis.py   # Motion intervals and formula cards
eureka_motion_story.py      # Evidence-grounded four-part AI story
eureka_physics_principle.py # Physics law concept cards
eureka_ai_tutor.py          # Local physics summaries and OpenAI support
app.py, main.py, ...        # Legacy ForgeHacks labs and utilities
hand_landmarker.task        # MediaPipe model for classic hand lab
assets/                     # Original screenshots and supporting assets
requirements.txt
.env.example
```

Runtime recordings in `experiments/`, plots in `comparisons/`, local `.env`, cache and backup files should not be committed.

## Demo and submission

- **ForgeHacks 2026**: previous version, available in the repository history; earlier submission at https://devpost.com/software/physilearn
- **EurekaDev 2026**: expanded version. Add the EurekaDev video and submission URL here after recording and submission.

## AI-assisted development disclosure

The author used ChatGPT for development support including debugging, code generation and patches, interface iteration, and documentation. The project was developed and tested interactively with real webcam experiments. Core physics metrics are calculated by Python rather than by a generative model. Earlier ForgeHacks code was reused and expanded for EurekaDev; this prior work is disclosed rather than presented as newly authored from scratch.

## Author

GitHub: [msns4](https://github.com/msns4)

**PhysiLearn — turn everyday motion into measurable physics.**
