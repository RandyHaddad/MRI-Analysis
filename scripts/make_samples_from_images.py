#!/usr/bin/env python3
import random
from pathlib import Path

try:
    from PIL import Image
except Exception as e:
    raise SystemExit("Missing Pillow. Install with: pip install Pillow")

ROOT = Path(__file__).resolve().parents[1]
ORG = ROOT / "IMAGES_ORGANIZED"
OUT = ORG / "SAMPLES" / "PATDEMO" / "STDEMO"


def find_series(base: Path):
    for pat in base.glob("PAT*"):
        for st in pat.glob("ST*"):
            for series in st.iterdir():
                if series.is_dir() and any(series.glob("*.jpg")):
                    yield series


def choose_series(series_paths):
    # Prefer series with 24 images; fall back to any
    with_counts = []
    for s in series_paths:
        n = len(list(s.glob("*.jpg")))
        with_counts.append((n, s))
    # Filter for exactly 24
    preferred = [s for n, s in with_counts if n == 24]
    if len(preferred) >= 3:
        return preferred[:3]
    # else take up to 3 across all
    return [s for _, s in sorted(with_counts, key=lambda x: -x[0])[:3]]


def crop_center(img: Image.Image, margin_ratio: float = 0.12) -> Image.Image:
    w, h = img.size
    mx = int(w * margin_ratio)
    my = int(h * margin_ratio)
    box = (mx, my, w - mx, h - my)
    return img.crop(box)


def save_samples(series_dir: Path, out_root: Path):
    out_dir = out_root / series_dir.name
    out_dir.mkdir(parents=True, exist_ok=True)
    imgs = sorted(series_dir.glob("*.jpg"))
    # Choose first, middle, and last for variety
    picks = [0, len(imgs) // 2, len(imgs) - 1]
    used = set()
    for idx in picks:
        idx = max(0, min(idx, len(imgs) - 1))
        if idx in used:
            continue
        used.add(idx)
        src = imgs[idx]
        with Image.open(src) as im:
            im = im.convert("RGB")
            im = crop_center(im, 0.12)
            im.thumbnail((512, 512))
            out = out_dir / src.name
            im.save(out, format="JPEG", quality=85)
    return out_dir


def main():
    series = list(find_series(ORG))
    if not series:
        raise SystemExit(f"No series found under {ORG}")
    chosen = choose_series(series)
    print("Chosen sample series:")
    for s in chosen:
        print(" -", s)
    for s in chosen:
        out = save_samples(s, OUT)
        print("Wrote samples to", out)


if __name__ == "__main__":
    main()

