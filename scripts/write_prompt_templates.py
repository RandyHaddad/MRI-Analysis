#!/usr/bin/env python3
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[1]
ORG_ROOT = ROOT / "IMAGES_ORGANIZED"

SYSTEM_PROMPT = (
    "You are a board-certified radiologist. You will receive one MRI series (all frames) plus contextual metadata for that series only. Produce a complete, clinically useful radiology report strictly from the provided images. Do not assume patient demographics or additional sequences beyond what is supplied. If critical sequences for a conclusion are missing, explicitly state the limitation rather than inferring findings.\n\n"
    "Requirements:\n"
    "- Use only the provided series and metadata. Do not rely on external knowledge of this patient.\n"
    "- Consider every frame; mention significant artifacts or technical limitations.\n"
    "- If the series label could be ambiguous, consider the POSSIBLE PARTS list (other series in the same study with identical frame counts) to frame your certainty, but base findings solely on the images you are given.\n"
    "- Be precise and reproducible: specify levels (e.g., L4–L5), sides (right/left), compartments (central canal, lateral recess, foramina), marrow signal, discs, alignment, soft tissues, sacroiliac joints as applicable to the anatomic region.\n"
    "- Avoid hallucinations. If a structure cannot be assessed, say ‘not adequately evaluated on this series.’\n"
    "- Report in Markdown with these section headings, in this order:\n"
    "  - Technique: planes, sequence type if inferable, frame count, and notable parameters or artifacts.\n"
    "  - Series Summary: what anatomy is covered and typical purpose of this sequence.\n"
    "  - Findings: structured, region-by-region with concise, clinically oriented statements.\n"
    "  - Impression: numbered, prioritized conclusions with level/side and severity; call out urgent/critical items first.\n"
    "  - Recommendations: further imaging or clinical correlation if warranted.\n"
    "  - Patient-friendly explanation: a brief, accessible summary for a non-medical reader.\n"
    "- Tone: clear, concise, and definitive where supported; qualify uncertainty with rationale. No preamble or disclaimers outside the above structure."
)


def list_series_folders(base: Path) -> List[Path]:
    folders = []
    if not base.exists():
        return folders
    for p in base.glob("PAT*/*/*"):
        if p.is_dir() and any(p.glob("*.jpg")):
            folders.append(p)
    return folders


def possible_parts_for(folder: Path) -> List[str]:
    study = folder.parent
    this_count = len(list(folder.glob("*.jpg")))
    parts = []
    for sib in study.iterdir():
        if sib.is_dir() and sib != folder and len(list(sib.glob("*.jpg"))) == this_count:
            parts.append(sib.name)
    return sorted(parts)


def write_templates(folder: Path):
    pat = folder.parent.parent.name
    study = folder.parent.name
    series = folder.name
    imgs = sorted(folder.glob("*.jpg"))
    n = len(imgs)
    parts = possible_parts_for(folder)

    # system prompt
    (folder / "system_prompt.txt").write_text(SYSTEM_PROMPT, encoding="utf-8")

    # user message template
    user_msg = []
    user_msg.append(f"Patient code: {pat}")
    user_msg.append(f"Study code: {study}")
    user_msg.append(f"Series label: {series}")
    user_msg.append(f"Frame count: {n}")
    user_msg.append("")
    user_msg.append("POSSIBLE PARTS (same frame count in this study):")
    if parts:
        for name in parts:
            user_msg.append(f"- {name}")
    else:
        user_msg.append("- None")
    user_msg.append("")
    user_msg.append("You will receive all frames attached (send all images in one message). Analyze every frame. Follow the system instructions and produce the report in Markdown using the required sections and order.")

    (folder / "user_message_template.md").write_text("\n".join(user_msg), encoding="utf-8")


def main():
    folders = list_series_folders(ORG_ROOT)
    if not folders:
        raise SystemExit(f"No series folders with images found under {ORG_ROOT}")
    for f in folders:
        write_templates(f)
        print(f"Wrote prompts in: {f}")


if __name__ == "__main__":
    main()

