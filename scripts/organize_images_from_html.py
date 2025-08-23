#!/usr/bin/env python3
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML_LIST = ROOT / "HTML" / "ListeSeries.htm"
IMAGES_ROOT = ROOT / "IMAGES"
OUT_ROOT = ROOT / "IMAGES_ORGANIZED"


def sanitize(name: str) -> str:
    # Remove/replace characters not suitable for Windows paths
    name = name.replace("/", "-")
    name = name.replace("\\", "-")
    name = name.replace(":", " -")
    name = name.replace("*", "x")
    name = name.replace("?", "")
    name = name.replace("\"", "'")
    name = name.replace("<", "(")
    name = name.replace(">", ")")
    name = name.replace("|", "-")
    name = name.strip()
    # Collapse repeated spaces
    name = re.sub(r"\s+", " ", name)
    return name


def parse_series_from_html(html_text: str):
    # We expect repeating blocks:
    # <a href="../IMAGES/PAT00000/ST000000/SE000000/Series.htm" ...></a>
    # ... then shortly after ...
    # <td width="40%" align="center">Label (N Images)</td>
    pattern = re.compile(
        r"href=\"\.\.\/IMAGES\/(PAT\d+)\/(ST\d+)\/(SE\d+)\/Series\.htm\"[\s\S]*?<td[^>]*>([^<]+)<\/td>",
        re.IGNORECASE,
    )
    mappings = []
    for m in pattern.finditer(html_text):
        pat, st, se, label = m.groups()
        label = sanitize(label)
        mappings.append({
            "patient": pat,
            "study": st,
            "series": se,
            "label": label,
        })
    return mappings


def copy_series(mappings):
    OUT_ROOT.mkdir(exist_ok=True)
    # Track used labels per study to avoid collisions
    used = {}
    for item in mappings:
        pat = item["patient"]
        st = item["study"]
        se = item["series"]
        label = item["label"]

        src = IMAGES_ROOT / pat / st / se
        if not src.exists():
            print(f"WARN: source not found: {src}")
            continue

        # Avoid duplicate folder names within same patient/study
        key = (pat, st, label)
        final_label = label
        if key not in used:
            used[key] = 1
        else:
            used[key] += 1
            # Append series code to keep uniqueness while preserving label
            final_label = f"{label} ({se})"

        dst = OUT_ROOT / pat / st / final_label
        dst.mkdir(parents=True, exist_ok=True)

        # Copy all files from series directory (mostly JPG + Series.htm)
        for p in src.iterdir():
            if p.is_file():
                shutil.copy2(p, dst / p.name)

        print(f"Copied {src} -> {dst}")


def main():
    if not HTML_LIST.exists():
        raise SystemExit(f"Not found: {HTML_LIST}")
    html = HTML_LIST.read_text(encoding="iso-8859-1", errors="ignore")
    mappings = parse_series_from_html(html)
    if not mappings:
        raise SystemExit("No series found in HTML/ListeSeries.htm")
    copy_series(mappings)


if __name__ == "__main__":
    main()

