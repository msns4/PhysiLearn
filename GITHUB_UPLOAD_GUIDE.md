# Updating your existing GitHub repository (msns4/PhysiLearn)

This ZIP is a **prepared source snapshot**, not a live GitHub update. Do not upload the ZIP itself as the only repo file.

1. Back up your working folder `C:\PhysiLearn-Eureka` before applying any replacements.
2. Extract these files into a SEPARATE staging folder; do not overwrite your tested Windows copy just to prepare the release.
3. Check and compare any README, dependencies and `.gitignore` edits. The supplied `requirements.txt` is UTF-8 (your collected original was UTF-16).
4. The original GitHub repository **already has** `assets/` and `hand_landmarker.task`; leave those in place because the legacy labs need them.
5. Keep `.env` on your own computer. Do not upload it or any API keys, recording data, webcam photos/videos or backups.
6. Review the source diff, then add the new EurekaDev files and update docs using GitHub Desktop, VS Code git, or the GitHub web UI.
7. Test a fresh clone using Python 3.12, `pip install -r requirements.txt` and `python app_eureka.py` before submitting to EurekaDev.
8. Keep the old `app.py`, and disclose that the ForgeHacks foundation was reused and extended.

Files intentionally **excluded** from this package: the duplicate `eureka_motion_analysis (1).py`; `assets/` and `hand_landmarker.task` (already in existing GitHub repo); any local `.env`, personal recordings, outputs, and backups.
