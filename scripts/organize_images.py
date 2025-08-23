#!/usr/bin/env python3
"""
Organize MRI image folders into IMAGES_ORGANIZED using category→count mapping parsed
from Agents.md (or AGENTS.md). Each category is matched to a source folder by the
number of image files it contains. Folders are copied (not modified).

Usage examples:
  python scripts/organize_images.py \
    --images-root IMAGES \
    --agents-file Agents.md \
    --out-dir IMAGES_ORGANIZED \
    --copy

  Dry-run preview only:
  python scripts/organize_images.py -n
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple


IMAGE_EXTS = {
    ".dcm",
    ".nii",
    ".nii.gz",
    ".png",
    ".jpg",
    ".jpeg",
    ".tif",
    ".tiff",
    ".bmp",
}


def is_image_file(p: Path) -> bool:
    if p.is_dir():
        return False
    name = p.name.lower()
    if name.startswith("."):
        return False
    # Handle compound extensions like .nii.gz
    if name.endswith(".nii.gz"):
        return True
    return p.suffix.lower() in IMAGE_EXTS


def parse_agents_counts(agents_path: Path) -> Dict[str, int]:
    text = agents_path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    mapping: Dict[str, int] = {}

    # Patterns: support common Markdown list/table styles
    pat_colon = re.compile(r"^\s*[-*]?\s*(.+?)\s*[:\-–]\s*(\d+)\s*(?:images?)?\s*$", re.IGNORECASE)
    pat_paren = re.compile(r"^\s*[-*]?\s*(.+?)\s*\((\d+)\)\s*(?:images?)?\s*$", re.IGNORECASE)
    pat_table = re.compile(r"^\|\s*(.+?)\s*\|\s*(\d+)\s*\|", re.IGNORECASE)

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        for pat in (pat_colon, pat_paren, pat_table):
            m = pat.match(line)
            if m:
                name, count = m.group(1).strip(), int(m.group(2))
                # Normalize multiple spaces
                name = re.sub(r"\s+", " ", name)
                mapping[name] = count
                break

    # If nothing found, return empty mapping and let caller fallback gracefully
    return mapping


def count_images_in_folder(folder: Path) -> int:
    if not folder.is_dir():
        return 0
    count = 0
    # Recursive count; skip hidden dirs
    for root, dirs, files in os.walk(folder):
        # prune hidden dirs
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for fname in files:
            if fname.startswith('.'):
                continue
            p = Path(root) / fname
            if is_image_file(p):
                count += 1
    if count == 0:
        # Fallback: count all non-hidden files recursively
        for root, dirs, files in os.walk(folder):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for fname in files:
                if not fname.startswith('.'):
                    count += 1
    return count


def scan_source_folders(images_root: Path) -> Dict[Path, int]:
    if not images_root.exists():
        raise FileNotFoundError(f"Images root not found: {images_root}")
    folders = [p for p in images_root.iterdir() if p.is_dir()]
    if not folders:
        raise ValueError(f"No subfolders found under {images_root}")
    counts: Dict[Path, int] = {}
    for f in sorted(folders):
        counts[f] = count_images_in_folder(f)
    return counts


def build_mapping(
    cat_to_count: Dict[str, int], folder_to_count: Dict[Path, int]
) -> Tuple[List[Tuple[str, Path]], List[str], List[Path]]:
    """
    Returns (matches, unused_categories, unmatched_folders)
    - matches: list of (category_name, source_folder)
    Deterministic: alphabetic order for categories and path order for folders.
    """
    count_to_cats: Dict[int, List[str]] = defaultdict(list)
    for cat, c in cat_to_count.items():
        count_to_cats[c].append(cat)
    for c in count_to_cats:
        count_to_cats[c].sort(key=lambda s: s.lower())

    count_to_folders: Dict[int, List[Path]] = defaultdict(list)
    for folder, c in folder_to_count.items():
        count_to_folders[c].append(folder)
    for c in count_to_folders:
        count_to_folders[c].sort()

    matches: List[Tuple[str, Path]] = []
    unused_categories: List[str] = []
    unmatched_folders: List[Path] = []

    all_counts = set(count_to_cats.keys()) | set(count_to_folders.keys())
    for c in sorted(all_counts):
        cats = count_to_cats.get(c, [])
        folders = count_to_folders.get(c, [])
        if not cats and folders:
            unmatched_folders.extend(folders)
            continue
        if cats and not folders:
            unused_categories.extend(cats)
            continue

        # Pair deterministically one-by-one
        n = min(len(cats), len(folders))
        for i in range(n):
            matches.append((cats[i], folders[i]))
        # Remainders
        if len(cats) > n:
            unused_categories.extend(cats[n:])
        if len(folders) > n:
            unmatched_folders.extend(folders[n:])

    return matches, unused_categories, unmatched_folders


def copy_tree(src: Path, dst: Path) -> None:
    for root, dirs, files in os.walk(src):
        rel = Path(root).relative_to(src)
        target_dir = dst / rel
        target_dir.mkdir(parents=True, exist_ok=True)
        for fname in files:
            if fname.startswith('.'):
                continue
            s = Path(root) / fname
            d = target_dir / fname
            shutil.copy2(s, d)


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Organize IMAGES into IMAGES_ORGANIZED by category counts")
    parser.add_argument("--images-root", default="IMAGES", type=Path, help="Root folder containing source series folders")
    parser.add_argument(
        "--agents-file",
        default=None,
        type=Path,
        help="Path to Agents.md (or AGENTS.md). If omitted, auto-detect.",
    )
    parser.add_argument("--out-dir", default="IMAGES_ORGANIZED", type=Path, help="Output folder to create")
    parser.add_argument("--move", action="store_true", help="Move instead of copy (destructive). Default is copy.")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Preview actions without writing files")
    args = parser.parse_args(argv)

    agents_file = args.agents_file
    if agents_file is None:
        # Prefer 'Agents.md'; fallback to 'AGENTS.md'
        for cand in (Path("Agents.md"), Path("AGENTS.md")):
            if cand.exists():
                agents_file = cand
                break
        if agents_file is None:
            print("ERROR: Could not find Agents.md or AGENTS.md at repo root.", file=sys.stderr)
            return 2

    # Parse Agents.md if available; allow empty mapping (fallback mode)
    try:
        cat_to_count = parse_agents_counts(agents_file)
    except Exception as e:
        print(f"WARNING: Failed to parse {agents_file}: {e}", file=sys.stderr)
        cat_to_count = {}

    try:
        folder_to_count = scan_source_folders(args.images_root)
    except Exception as e:
        print(f"ERROR scanning {args.images_root}: {e}", file=sys.stderr)
        return 2

    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    if cat_to_count:
        # Category-directed mode
        matches, unused_categories, unmatched_folders = build_mapping(cat_to_count, folder_to_count)

        print("Planned matches (category ← folder):")
        for cat, folder in matches:
            print(f"  {cat}  ←  {folder.name}  (count={folder_to_count[folder]})")
        if unused_categories:
            print("Unused categories (no folder count match):")
            for cat in unused_categories:
                print(f"  - {cat} (count={cat_to_count[cat]})")
        if unmatched_folders:
            print("Unmatched folders (no category count match):")
            for f in unmatched_folders:
                print(f"  - {f.name} (count={folder_to_count[f]})")

        if args.dry_run:
            print("Dry-run: no files written.")
            return 0

        # Execute copies/moves for matched pairs
        for cat, src_folder in matches:
            dst_folder = out_dir / cat
            if args.move:
                if dst_folder.exists():
                    for item in src_folder.iterdir():
                        shutil.move(str(item), str(dst_folder / item.name))
                else:
                    shutil.move(str(src_folder), str(dst_folder))
            else:
                dst_folder.mkdir(parents=True, exist_ok=True)
                copy_tree(src_folder, dst_folder)

        # Handle unmatched: keep a record for manual review
        if unmatched_folders:
            review_dir = out_dir / "UNMATCHED"
            review_dir.mkdir(parents=True, exist_ok=True)
            for src in unmatched_folders:
                hint = f"{src.name}_count-{folder_to_count[src]}"
                placeholder = review_dir / hint
                placeholder.mkdir(exist_ok=True)
                note = placeholder / "README.txt"
                note.write_text(
                    f"Source folder: {src}\nFiles counted: {folder_to_count[src]}\nMove/copy manually to the correct category.",
                    encoding="utf-8",
                )

        manifest = out_dir / "MANIFEST.txt"
        with manifest.open("w", encoding="utf-8") as fh:
            for cat, src_folder in matches:
                fh.write(f"{src_folder} -> {cat}\n")
            if unmatched_folders:
                fh.write("\nUnmatched folders:\n")
                for f in unmatched_folders:
                    fh.write(f"{f} (count={folder_to_count[f]})\n")

        print(f"\nDone. Output at: {out_dir}\nManifest: {manifest}")
        return 0

    # Fallback: no categories found; organize by count only
    print("No categories found in Agents.md; organizing by counts only.")
    print("Each source folder will be copied under IMAGES_ORGANIZED/count-<N>/<original-name>.")

    if args.dry_run:
        for folder, cnt in folder_to_count.items():
            print(f"Would copy {folder.name} -> count-{cnt}/{folder.name}")
        print("Dry-run: no files written.")
        return 0

    for folder, cnt in folder_to_count.items():
        dst = out_dir / f"count-{cnt}" / folder.name
        dst.mkdir(parents=True, exist_ok=True)
        copy_tree(folder, dst)

    manifest = out_dir / "MANIFEST.txt"
    with manifest.open("w", encoding="utf-8") as fh:
        for folder, cnt in folder_to_count.items():
            fh.write(f"{folder} -> count-{cnt}/{folder.name}\n")
    print(f"\nDone (count-only mode). Output at: {out_dir}\nManifest: {manifest}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
