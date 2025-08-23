# Repository Guidelines

## Project Structure & Module Organization
- `dicom/` or `nifti/`: Source MRI files (read‑only; keep raw immutable).
- `metadata/`: CSV/JSON sidecars, cohort lists, and labels.
- `processed/`: Derived outputs (e.g., skull‑stripped, resampled). Do not commit large intermediates unless essential.
- `notebooks/`: Exploratory analysis (`*.ipynb`). Keep data paths relative.
- `scripts/`: Reproducible pipelines and utilities (Python/CLI).
- `tests/`: Unit tests for scripts and pipelines.
- `docs/`: Notes, study protocols, and figures.

## Build, Test, and Development Commands
- Create env: `python -m venv .venv && . .venv/bin/activate` (Windows PowerShell: `.venv\\Scripts\\Activate.ps1`).
- Install deps (if present): `pip install -r requirements.txt`.
- Run checks: `pytest -q` (tests), `ruff check .` (lint), `black .` (format).
- Convert DICOM→NIfTI (example): `python scripts/dicom_to_nifti.py --in dicom/ --out nifti/`.

## Coding Style & Naming Conventions
- Python style: PEP 8; format with `black` (88 cols), lint with `ruff`.
- Indentation: 4 spaces; UTF‑8; Unix newlines.
- Names: lower_snake_case for files/modules; UpperCamelCase for classes; lower_snake_case for functions/vars.
- Data artifacts: use kebab‑case with modality and subject ID, e.g., `sub-001_t1w.nii.gz`.

## Testing Guidelines
- Framework: `pytest` with tests in `tests/` mirroring `scripts/`.
- Naming: `test_<module>.py` and `Test<ClassName>`; use fixtures for sample data under `tests/data/` (small, anonymized).
- Coverage: target ≥80% for core utilities (I/O, transforms). Run `pytest --cov=scripts`.

## Commit & Pull Request Guidelines
- Commits: imperative present, ≤72‑char subject. Examples: `add dicom→nifti converter`, `fix nifti header orientation`.
- Scope small; reference issues like `Refs #12`.
- PRs: include purpose, approach, sample command, before/after metrics or screenshots; note dataset provenance and any schema changes.

## Security & Configuration Tips
- PHI/PII: ensure DICOM de‑identification before commit; never upload raw hospital identifiers.
- `.gitignore`: exclude large intermediates (`processed/`, `*.nii`, `*.zip`) unless explicitly needed.
- Reproducibility: pin versions in `requirements.txt`; set seeds in scripts; prefer relative paths anchored at repo root.


## Categories of Images

EL HADDAD^RANDY MITRI
L-SPINE MRI (8/21/2025) - MR

3-Plane Localizer (27 Images)

Sag T2 FSE 4mm (17 Images)

Sag T1 FSE 4mm (17 Images)

Sag T2 STIR 4mm (17 Images)

Ax T2 frFSE (23 Images)

Ax T1 FSE (23 Images)

Ax T2 frFSE BLOCK (42 Images)

--------------

EL HADDAD^RANDY MITRI
SACRO-ILIAC MRI (8/21/2025) - MR
3-Plane Localizer (17 Images)

3-Plane Localizer (17 Images)

Cor T2 STIR BIG FOV (31 Images)

Cor T1 FSE BIG FOV (31 Images)

Ax STIR (30 Images)

COR STIR (24 Images)

Cor T1 FSE (24 Images)

COR T2 frFSE (24 Images)

Ax T1 FSE (30 Images)

Ax DWI B-100/800/1000 (81 Images)

Ax T2* MERGE (30 Images)

ADC (10^-6 mmÂ²/s) (27 Images)

ORIG Ax DWI B-100/800/1000 (81 Images)