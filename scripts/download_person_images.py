#!/usr/bin/env python3
"""Download public images for a person using DuckDuckGo Images (no API key).

Example:
  python scripts/download_person_images.py "Scarlett Johansson" --num 20 --orientation horizontal
"""

from __future__ import annotations

import argparse
import re
import sys
from io import BytesIO
from pathlib import Path
from typing import Literal

try:
    import requests
    from duckduckgo_search import DDGS
    from PIL import Image, ImageOps
except ModuleNotFoundError as e:
    missing = getattr(e, "name", None) or "a required dependency"
    print(
        "Missing dependency for image download script.\n"
        f"  Missing: {missing}\n"
        '  Install: pip install -e ".[images]"  (or: pip install duckduckgo-search Pillow requests)',
        file=sys.stderr,
    )
    raise SystemExit(2) from e

Orientation = Literal["horizontal", "vertical", "any"]


def _slugify_folder(name: str) -> str:
    name = name.strip()
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"[^A-Za-z0-9_\-]+", "", name)
    return name or "images"


def _open_image(image_bytes: bytes) -> Image.Image | None:
    try:
        img = Image.open(BytesIO(image_bytes))
        img = ImageOps.exif_transpose(img)
        img.load()
        return img
    except Exception:
        return None


def _matches_orientation(img: Image.Image, orientation: Orientation) -> bool:
    if orientation == "any":
        return True
    w, h = img.size
    if w == h:
        return False  # ignore square images for deterministic filtering
    if orientation == "horizontal":
        return w > h
    return h > w


def _save_as_jpeg(img: Image.Image, path: Path) -> None:
    # Convert to RGB to avoid issues with PNG/WebP alpha modes when saving JPG.
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    elif img.mode == "L":
        # keep grayscale; PIL will still write a valid JPEG
        pass
    img.save(path, format="JPEG", quality=92, optimize=True)


def download_person_images(
    person_name: str,
    num_images: int,
    orientation: Orientation,
    out_dir: Path,
    *,
    max_results: int = 100,
    region: str = "wt-wt",
    safesearch: str = "moderate",
    size: str = "Large",
    timeout_sec: float = 12.0,
    verbose: bool = False,
) -> int:
    if not person_name.strip():
        raise ValueError("person_name cannot be empty")
    if num_images <= 0:
        raise ValueError("num_images must be >= 1")

    folder = out_dir / _slugify_folder(person_name)
    folder.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update(
        {
            # Slightly reduces blocks/403s vs default python-requests UA.
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
    )

    downloaded = 0
    seen_urls: set[str] = set()

    with DDGS() as ddgs:
        results = ddgs.images(
            keywords=person_name,
            region=region,
            safesearch=safesearch,
            size=size,
            max_results=max_results,
        )

        for result in results:
            if downloaded >= num_images:
                break

            url = (result or {}).get("image") or ""
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)

            try:
                resp = session.get(url, timeout=timeout_sec)
                resp.raise_for_status()
                content_type = (resp.headers.get("content-type") or "").lower()
                if content_type and "image/" not in content_type:
                    continue

                img = _open_image(resp.content)
                if img is None:
                    continue
                if not _matches_orientation(img, orientation):
                    continue

                out_path = folder / f"{folder.name}_{downloaded + 1:03}.jpg"
                _save_as_jpeg(img, out_path)
                downloaded += 1

                print(f"Saved: {out_path} ({img.width}x{img.height})")

            except Exception as e:
                if verbose:
                    print(f"Skip: {url} ({type(e).__name__}: {e})")
                continue

    if downloaded < num_images:
        print(f"Warning: only downloaded {downloaded}/{num_images} images into {folder}")
        return 1

    print(f"Done: downloaded {downloaded}/{num_images} images into {folder}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download images of a person from DuckDuckGo Images (no API key)."
    )
    parser.add_argument(
        "name",
        help='Person name to search (e.g. "Scarlett Johansson").',
    )
    parser.add_argument(
        "--num",
        type=int,
        default=6,
        metavar="N",
        help="How many images to download (default: 6).",
    )
    parser.add_argument(
        "--orientation",
        choices=["horizontal", "vertical", "any"],
        default="horizontal",
        help="Filter by orientation (default: horizontal).",
    )
    parser.add_argument(
        "--out-dir",
        default=str(Path("output") / "images"),
        metavar="PATH",
        help="Base output directory (default: output/images).",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=100,
        metavar="N",
        help="Max image search results to scan (default: 100).",
    )
    parser.add_argument(
        "--region",
        default="wt-wt",
        metavar="CODE",
        help="DuckDuckGo region code (default: wt-wt).",
    )
    parser.add_argument(
        "--safesearch",
        default="moderate",
        choices=["off", "moderate", "strict"],
        help="SafeSearch level (default: moderate).",
    )
    parser.add_argument(
        "--size",
        default="Large",
        choices=["Small", "Medium", "Large", "Wallpaper"],
        help="Image size hint (default: Large).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=12.0,
        metavar="SECS",
        help="Per-request timeout in seconds (default: 12).",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print download errors for skipped URLs.",
    )
    args = parser.parse_args()

    exit_code = download_person_images(
        person_name=args.name,
        num_images=args.num,
        orientation=args.orientation,  # type: ignore[arg-type]
        out_dir=Path(args.out_dir),
        max_results=args.max_results,
        region=args.region,
        safesearch=args.safesearch,
        size=args.size,
        timeout_sec=args.timeout,
        verbose=args.verbose,
    )
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
