# MRI Report Pipeline (Spine & SI Series)

This repository organizes exported MRI series images and generates radiologist-style reports via OpenAI.

Important: Raw patient images and vendor CD assets are excluded from the repo to avoid uploading PHI and large binaries. The scripts operate on your local files.

## Layout
- `scripts/`: Utilities to organize series, write prompt templates, and generate reports.
- `processed/reports/`: Generated `report.md` per series (kept in repo; adjust `.gitignore` if you prefer to exclude).
- `metadata/`, `docs/`, `tests/`, `notebooks/`: Reserved for cohort metadata, notes, tests, and exploration (empty placeholders).

Raw assets expected locally (git-ignored):
- `IMAGES/` and `HTML/` from the CD export.
- `IMAGES_ORGANIZED/` created by the organizer script.

## Quickstart
1) Create env
```
python -m venv .venv
. .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
```

2) Install deps
```
pip install -r requirements.txt
```

3) Organize images into labeled folders (reads HTML/ListeSeries.htm)
```
python scripts/organize_images_from_html.py
```
This creates `IMAGES_ORGANIZED/PATxxxx/STxxxx/<Series label (N Images)>/` and copies series JPGs there.

4) Write per-series prompt templates (system + user)
```
python scripts/write_prompt_templates.py
```
This places `system_prompt.txt` and `user_message_template.md` in each series folder.

5) Generate AI reports for each series
```
# Option A: use environment variable
$env:OPENAI_API_KEY = "<your_key>"   # PowerShell
export OPENAI_API_KEY="<your_key>"   # bash/zsh

python scripts/generate_reports.py --model gpt-5 --fallback-model gpt-4o
```
Outputs `processed/reports/PATxxxx/STxxxx/<Series>/report.md`.

## Notes & Safety
- PHI: Do not commit `IMAGES/`, `IMAGES_ORGANIZED/`, or `HTML/`. The `.gitignore` enforces this by default.
- POSSIBLE PARTS: The generator includes sibling series with identical frame counts as context.
- Idempotent: Scripts are re-runnable; originals are not modified.
- Models: Defaults try `gpt-5`, then `gpt-4o` if unavailable in your account/region.

## Development
- Format: `black .` (88 cols)
- Lint: `ruff check .`
- Tests: `pytest -q`

## Troubleshooting
- If `ListeSeries.htm` isn’t present or has a different path, update `scripts/organize_images_from_html.py` (`HTML/ListeSeries.htm`).
- If folder names contain unsupported characters on Windows, the organizer sanitizes them (e.g., `/` → `-`, `*` → `x`).

***

This repo was scaffolded from a vendor MRI CD export to enable reproducible, local reporting without uploading raw images to GitHub.
