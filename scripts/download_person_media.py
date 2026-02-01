#!/usr/bin/env python3
"""Download public images (and optionally short videos) for a person using DuckDuckGo (no API key).

Examples:
  python scripts/download_person_media.py "Scarlett Johansson" --num 20 --orientation horizontal
  python scripts/download_person_media.py "Scarlett Johansson" --num 20 --orientation horizontal --videos
"""

from __future__ import annotations

import argparse
import re
import sys
from io import BytesIO
from pathlib import Path
from typing import Any, Literal

Orientation = Literal["horizontal", "vertical", "any"]
VideoContainer = Literal["mp4", "webm", "mov", "mkv", "m4v", "avi", "unknown"]


def _require_deps() -> tuple[Any, Any, Any, Any]:
    """Import optional dependencies only when needed."""
    try:
        import requests  # type: ignore
        from duckduckgo_search import DDGS  # type: ignore
        from PIL import Image, ImageOps  # type: ignore
    except ModuleNotFoundError as e:
        missing = getattr(e, "name", None) or "a required dependency"
        print(
            "Missing dependency for media download script.\n"
            f"  Missing: {missing}\n"
            '  Install: pip install -e ".[images]"  (or: pip install duckduckgo-search Pillow requests)',
            file=sys.stderr,
        )
        raise SystemExit(2) from e
    return requests, DDGS, Image, ImageOps


def _slugify_folder(name: str) -> str:
    name = name.strip()
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"[^A-Za-z0-9_\-]+", "", name)
    return name or "media"


def _open_image(image_bytes: bytes) -> Any | None:
    _, _, Image, ImageOps = _require_deps()
    try:
        img = Image.open(BytesIO(image_bytes))
        img = ImageOps.exif_transpose(img)
        img.load()
        return img
    except Exception:
        return None


def _matches_orientation(img: Any, orientation: Orientation) -> bool:
    if orientation == "any":
        return True
    w, h = img.size
    if w == h:
        return False  # ignore square images for deterministic filtering
    if orientation == "horizontal":
        return w > h
    return h > w


def _save_as_jpeg(img: Any, path: Path) -> None:
    # Convert to RGB to avoid issues with PNG/WebP alpha modes when saving JPG.
    if getattr(img, "mode", "") not in ("RGB", "L"):
        img = img.convert("RGB")
    img.save(path, format="JPEG", quality=92, optimize=True)


def _guess_video_ext(url: str, content_type: str) -> VideoContainer:
    ct = (content_type or "").lower()
    if "video/mp4" in ct:
        return "mp4"
    if "video/webm" in ct:
        return "webm"
    if "video/quicktime" in ct:
        return "mov"
    u = (url or "").lower()
    for ext in ("mp4", "webm", "mov", "mkv", "m4v", "avi"):
        if u.split("?", 1)[0].endswith(f".{ext}"):
            return ext  # type: ignore[return-value]
    return "unknown"


def _download_stream_limited(
    session: Any,
    url: str,
    out_path: Path,
    *,
    timeout_sec: float,
    max_bytes: int,
) -> bool:
    """Download a URL to disk but abort if it exceeds max_bytes."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = out_path.with_suffix(out_path.suffix + ".part")
    bytes_written = 0
    try:
        with session.get(url, timeout=timeout_sec, stream=True) as resp:
            resp.raise_for_status()
            with open(tmp_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=256 * 1024):
                    if not chunk:
                        continue
                    bytes_written += len(chunk)
                    if bytes_written > max_bytes:
                        return False
                    f.write(chunk)
        tmp_path.replace(out_path)
        return True
    except Exception:
        return False
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except Exception:
                pass


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
    requests, DDGS, _, _ = _require_deps()

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

                print(f"Saved image: {out_path} ({img.width}x{img.height})")
            except Exception as e:
                if verbose:
                    print(f"Skip image: {url} ({type(e).__name__}: {e})")
                continue

    if downloaded < num_images:
        print(f"Warning: only downloaded {downloaded}/{num_images} images into {folder}")
        return 1

    print(f"Done: downloaded {downloaded}/{num_images} images into {folder}")
    return 0


def _require_ytdlp() -> Any:
    """Import yt-dlp only when needed."""
    try:
        import yt_dlp  # type: ignore
        return yt_dlp
    except ModuleNotFoundError as e:
        print(
            "Missing dependency for video download.\n"
            "  Missing: yt-dlp\n"
            '  Install: pip install -e ".[images]"  (or: pip install yt-dlp)',
            file=sys.stderr,
        )
        raise SystemExit(2) from e


def download_person_videos(
    person_name: str,
    num_videos: int,
    out_dir: Path,
    *,
    max_results: int = 50,
    region: str = "wt-wt",
    safesearch: str = "moderate",
    max_duration_sec: int = 60,
    verbose: bool = False,
) -> int:
    """Download short videos for a person using DuckDuckGo video search + yt-dlp.

    Searches DuckDuckGo for video URLs (YouTube, TikTok, etc.) and uses yt-dlp
    to download them. "Short" is enforced via max_duration_sec (default 120s).
    """
    _, DDGS, _, _ = _require_deps()
    yt_dlp = _require_ytdlp()

    if not person_name.strip():
        raise ValueError("person_name cannot be empty")
    if num_videos <= 0:
        raise ValueError("num_videos must be >= 1")
    if max_duration_sec <= 0:
        raise ValueError("max_duration_sec must be >= 1")

    folder = out_dir / _slugify_folder(person_name)
    folder.mkdir(parents=True, exist_ok=True)

    downloaded = 0
    seen_urls: set[str] = set()

    query = f"{person_name} short video"

    # Collect video URLs from DuckDuckGo
    video_urls: list[str] = []
    with DDGS() as ddgs:
        results = ddgs.videos(
            keywords=query,
            region=region,
            safesearch=safesearch,
            max_results=max_results,
        )
        for result in results:
            url = (result or {}).get("content") or (result or {}).get("href") or ""
            if url and url not in seen_urls:
                seen_urls.add(url)
                video_urls.append(url)

    if not video_urls:
        print(f"Warning: no video URLs found for '{person_name}'")
        return 1

    # yt-dlp options
    ydl_opts = {
        "format": "best[ext=mp4]/best",
        "outtmpl": str(folder / f"{_slugify_folder(person_name)}_%(autonumber)03d.%(ext)s"),
        "quiet": not verbose,
        "no_warnings": not verbose,
        "ignoreerrors": True,
        "noplaylist": True,
        "match_filter": yt_dlp.utils.match_filter_func(f"duration < {max_duration_sec}"),
    }

    print(f"Attempting to download up to {num_videos} videos (max {max_duration_sec}s each)...")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for url in video_urls:
            if downloaded >= num_videos:
                break

            try:
                # Extract info first to check duration
                info = ydl.extract_info(url, download=False)
                if info is None:
                    if verbose:
                        print(f"Skip video: {url} (could not extract info)")
                    continue

                duration = info.get("duration") or 0
                if duration > max_duration_sec:
                    if verbose:
                        print(f"Skip video: {url} (duration {duration}s > {max_duration_sec}s)")
                    continue

                # Download the video
                ydl.download([url])
                downloaded += 1
                title = info.get("title", url)[:50]
                print(f"Downloaded video {downloaded}: {title}")

            except Exception as e:
                if verbose:
                    print(f"Skip video: {url} ({type(e).__name__}: {e})")
                continue

    if downloaded < num_videos:
        print(f"Warning: only downloaded {downloaded}/{num_videos} videos into {folder}")
        return 1

    print(f"Done: downloaded {downloaded}/{num_videos} videos into {folder}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download images (and optionally short videos) of a person from DuckDuckGo (no API key)."
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
        help="How many images to download (and how many videos if --videos is set) (default: 6).",
    )
    parser.add_argument(
        "--videos",
        action="store_true",
        help="Also download short videos (same count as --num).",
    )
    parser.add_argument(
        "--orientation",
        choices=["horizontal", "vertical", "any"],
        default="horizontal",
        help="Filter images by orientation (default: horizontal).",
    )
    parser.add_argument(
        "--out-dir",
        default=str(Path("output") / "images"),
        metavar="PATH",
        help="Base output directory for images (default: output/images).",
    )
    parser.add_argument(
        "--videos-out-dir",
        default=str(Path("output") / "videos"),
        metavar="PATH",
        help="Base output directory for videos (default: output/videos).",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=100,
        metavar="N",
        help="Max image search results to scan (default: 100).",
    )
    parser.add_argument(
        "--video-max-results",
        type=int,
        default=50,
        metavar="N",
        help="Max video search results to scan (default: 50).",
    )
    parser.add_argument(
        "--max-video-duration",
        type=int,
        default=60,
        metavar="SECS",
        help="Max video duration in seconds (default: 60). Videos longer than this are skipped.",
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

    exit_code_img = download_person_images(
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

    exit_code_vid = 0
    if args.videos:
        exit_code_vid = download_person_videos(
            person_name=args.name,
            num_videos=args.num,
            out_dir=Path(args.videos_out_dir),
            max_results=args.video_max_results,
            region=args.region,
            safesearch=args.safesearch,
            max_duration_sec=args.max_video_duration,
            verbose=args.verbose,
        )

    raise SystemExit(max(exit_code_img, exit_code_vid))


if __name__ == "__main__":
    main()

