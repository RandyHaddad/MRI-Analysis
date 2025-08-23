#!/usr/bin/env python3
import argparse
import base64
import json
import os
import time
from pathlib import Path
from typing import List, Dict

import requests

ROOT = Path(__file__).resolve().parents[1]
ORG_ROOT = ROOT / "IMAGES_ORGANIZED"
REPORT_ROOT = ROOT / "processed" / "reports"


def list_series_folders(base: Path) -> List[Path]:
    folders = []
    # Expect: PATxxxx/STxxxx/<series label>/IMG*.jpg
    if not base.exists():
        return folders
    for p in base.glob("PAT*/*/*"):
        if p.is_dir():
            # contains images?
            imgs = list(p.glob("*.jpg"))
            if imgs:
                folders.append(p)
    return folders


def possible_parts_for(folder: Path) -> List[str]:
    # Siblings under same study (.. / STxxxx / *) with same image count
    study = folder.parent
    this_count = len(list(folder.glob("*.jpg")))
    parts = []
    for sib in study.iterdir():
        if sib.is_dir() and sib != folder:
            if len(list(sib.glob("*.jpg"))) == this_count:
                parts.append(sib.name)
    return sorted(parts)


def encode_images_as_data_urls(img_paths: List[Path]) -> List[Dict]:
    content = []
    for img in img_paths:
        with img.open("rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        data_url = f"data:image/jpeg;base64,{b64}"
        content.append({
            "type": "image_url",
            "image_url": {"url": data_url},
        })
    return content


def build_prompt(folder: Path, possible_parts: List[str]) -> List[Dict]:
    imgs = sorted(folder.glob("*.jpg"))
    series_name = folder.name
    study_code = folder.parent.name
    patient_code = folder.parent.parent.name
    n_imgs = len(imgs)

    text = f"""
You are a board-certified radiologist. Review the following MRI image set and draft a comprehensive radiology report for this one series.

Context:
- Patient code: {patient_code}
- Study code: {study_code}
- Series label: {series_name}
- Frame count: {n_imgs}
- POSSIBLE PARTS (other series with the same number of images in this study): {', '.join(possible_parts) if possible_parts else 'None'}

Instructions:
1) Do not assume demographics that are not shown.
2) If key sequences needed for a conclusion are missing, state limitations.
3) Use clear, concise language; be definitive where possible; qualify uncertainty with rationale.

Report format (use these section headings):
- Technique: acquisition planes, sequence type, relevant parameters if inferable, and frame count.
- Series Summary: what anatomy is covered and purpose of this sequence.
- Findings: structured, region-by-region. Include alignment, marrow, discs, canal/foramina, soft tissues, sacroiliac joints as relevant.
- Impression: numbered, prioritized conclusions; include level and side for focal findings.
- Recommendations: further imaging or clinical correlation if warranted.
- Patient-friendly explanation: a brief lay summary at the end.
""".strip()

    # Compose message content with text + images
    content: List[Dict] = [{"type": "text", "text": text}]
    content += encode_images_as_data_urls(imgs)
    return content


def call_openai_chat(api_key: str, model: str, content: List[Dict]) -> str:
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "messages": [{"role": "user", "content": content}],
        # Ensure long outputs are allowed
        "temperature": 0.2,
        "max_tokens": 2000,
    }
    resp = requests.post(url, headers=headers, data=json.dumps(body), timeout=180)
    if resp.status_code != 200:
        raise RuntimeError(f"OpenAI API error {resp.status_code}: {resp.text[:500]}")
    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()


def generate_report_for_folder(folder: Path, api_key: str, preferred_model: str, fallback_model: str) -> Path:
    parts = possible_parts_for(folder)
    content = build_prompt(folder, parts)

    # Try preferred model first, then fallback
    err = None
    for mdl in [preferred_model, fallback_model]:
        try:
            text = call_openai_chat(api_key, mdl, content)
            # Save
            out_dir = REPORT_ROOT / folder.relative_to(ORG_ROOT)
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / "report.md"
            out_file.write_text(text, encoding="utf-8")
            return out_file
        except Exception as e:
            err = e
            time.sleep(1.5)
            continue
    raise err if err else RuntimeError("Unknown error generating report")


def main():
    parser = argparse.ArgumentParser(description="Generate MRI series reports via OpenAI")
    parser.add_argument("--api-key", default=os.getenv("OPENAI_API_KEY"), help="OpenAI API key (or set OPENAI_API_KEY)")
    parser.add_argument("--organized-root", default=str(ORG_ROOT), help="Path to IMAGES_ORGANIZED root")
    parser.add_argument("--model", default="gpt-5", help="Preferred model")
    parser.add_argument("--fallback-model", default="gpt-4o", help="Fallback model if preferred fails")
    args = parser.parse_args()

    if not args.api_key:
        raise SystemExit("Missing API key. Pass --api-key or set OPENAI_API_KEY")

    base = Path(args.organized_root)
    folders = list_series_folders(base)
    if not folders:
        raise SystemExit(f"No image folders found under {base}")

    print(f"Found {len(folders)} series folders under {base}")
    for idx, folder in enumerate(folders, 1):
        print(f"[{idx}/{len(folders)}] Generating report for: {folder}")
        out = generate_report_for_folder(folder, args.api_key, args.model, args.fallback_model)
        print(f"  -> Wrote {out}")


if __name__ == "__main__":
    main()

