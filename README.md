# PhysiLearn

PhysiLearn is an interactive physics learning app that turns a webcam into a small motion laboratory.

Instead of giving students made-up numbers from a textbook, PhysiLearn measures real motion from a webcam, converts it into physics data, and creates personalized learning tasks from the student's own experiment.

Built for the **ForgeHacks Online 2026** AI + Education track.

---

## What PhysiLearn Does

PhysiLearn currently includes two interactive modes:

### Tennis Ball Physics Lab

A student rolls a tennis ball in front of a webcam.

PhysiLearn:

- detects and tracks the tennis ball with OpenCV
- estimates real-world scale using the approximate diameter of a tennis ball
- measures distance traveled
- measures displacement
- measures experiment time
- calculates average speed
- calculates average velocity
- estimates velocity and acceleration over time
- generates position, velocity, and acceleration graphs
- asks the student to calculate average speed using their own measured data

Example:

```text
Distance traveled: 0.443 m
Time: 3.169 s

v = d / t

v = 0.443 / 3.169
v ≈ 0.140 m/s
```

This turns a real experiment into a personalized physics problem.

---

### Hand Motion Challenge

The student moves their hand from left to right while trying to maintain approximately constant velocity.

MediaPipe tracks the hand while PhysiLearn measures:

- direction consistency
- velocity variation
- average acceleration

A deterministic physics evaluator then decides whether the motion passes the challenge.

The AI does not decide the grade.

Instead, the AI Physics Tutor explains the measured result and gives personalized feedback.

Example:

```text
Direction consistency: 67.5%
Velocity variation: 0.246
Average acceleration: 0.320

Result: TRY AGAIN
```

PhysiLearn can then explain that direction consistency missed the target while the other measurements passed.

---

## Why PhysiLearn

Physics is often taught using diagrams and fictional numbers.

PhysiLearn makes physics more interactive by letting students create the data themselves.

A student can:

1. perform a real motion experiment
2. see the motion tracked by computer vision
3. inspect real measurements
4. apply physics formulas
5. receive immediate feedback
6. understand how their movement affected the result

The goal is to connect physical intuition, mathematical formulas, and real-world experimentation.

---

## How It Works

### Tennis Ball Pipeline

```text
Webcam
   ↓
OpenCV color tracking
   ↓
Ball position over time
   ↓
Camera-based scale estimation
   ↓
Distance / displacement / time
   ↓
Speed / velocity / acceleration
   ↓
Physics graphs
   ↓
Student calculation challenge
```

### Hand Motion Pipeline

```text
Webcam
   ↓
MediaPipe hand tracking
   ↓
Hand position over time
   ↓
Velocity + acceleration
   ↓
Rule-based physics evaluator
   ↓
PASS / TRY AGAIN
   ↓
AI Physics Tutor
```

---

## AI Physics Tutor

PhysiLearn uses Featherless AI through an OpenAI-compatible API.

The AI is used only for explanation and personalized coaching.

It does not determine whether a physics experiment passes or fails.

The grading pipeline is intentionally separated:

```text
Computer Vision
      ↓
Physics Measurements
      ↓
Deterministic Evaluator
      ↓
Official Result
      ↓
AI Explanation
```

This keeps the physics evaluation reproducible while still allowing the AI to explain results in student-friendly language.

The tutor can explain concepts such as:

```text
v = Δx / Δt
a = Δv / Δt
```

and connect them to the student's measured motion.

---

## Technology

PhysiLearn is built with:

- Python
- OpenCV
- MediaPipe
- NumPy
- Matplotlib
- CustomTkinter
- Featherless AI
- OpenAI Python SDK
- python-dotenv

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/msns4/PhysiLearn.git
cd PhysiLearn
```

### 2. Create a virtual environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the AI Tutor

Copy:

```text
.env.example
```

to:

```text
.env
```

Then add your Featherless API key:

```text
FEATHERLESS_API_KEY=your_api_key_here
```

The real `.env` file is ignored by Git and should never be committed.

---

## Run PhysiLearn

Start the application with:

```bash
python app.py
```

A webcam is required.

---

## Ball Physics Lab

For the most reliable tennis-ball experiment:

- use a yellow-green tennis ball
- use a plain background
- avoid other bright yellow objects in the camera view
- keep the ball at roughly the same distance from the webcam
- roll the ball slowly enough for the camera to track it clearly

The current prototype estimates scale using the approximate physical diameter of a tennis ball.

Because the system uses a webcam rather than calibrated laboratory equipment, real-world measurements should be treated as approximate.

---

## Current Features

- webcam-based motion experiments
- tennis-ball tracking
- hand tracking
- camera-based scale estimation
- distance measurement
- displacement measurement
- average speed
- average velocity
- velocity and acceleration estimation
- position-time graph
- velocity-time graph
- acceleration-time graph
- interactive student calculation challenge
- PASS / TRY AGAIN physics evaluator
- personalized AI physics explanations
- API fallback behavior
- dark desktop UI

---

## Limitations

PhysiLearn is currently a hackathon prototype.

Current limitations include:

- tennis-ball tracking depends on lighting and background
- real-world scale is estimated from ball size and camera perspective
- measurements are not laboratory-grade
- the tennis ball should remain approximately in the same motion plane
- very fast objects may blur because of webcam frame rate
- the hand challenge currently focuses on one constant-velocity experiment
- the current UI is desktop-focused

---

## Future Work

Possible future improvements include:

- automatic object-color calibration
- additional physics experiments
- inclined-plane acceleration experiments
- free-fall experiments
- more object types
- calibrated measurement using reference markers
- interactive graph interpretation questions
- student progress tracking
- teacher dashboards
- web deployment
- additional AI-generated explanations and adaptive hints

---

## Project Philosophy

PhysiLearn is built around one idea:

> Physics becomes more meaningful when the numbers come from your own experiment.

Instead of only reading about motion, students can create it, measure it, calculate it, and understand it.

---

## Hackathon

Built for **ForgeHacks Online 2026**.

**Track:** AI + Education

---

## Author

Built by **Mansur Gapar**.