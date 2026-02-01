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
from collections import Counter
from io import BytesIO
from pathlib import Path
from typing import Any, Literal

Orientation = Literal["horizontal", "vertical", "any"]
VideoContainer = Literal["mp4", "webm", "mov", "mkv", "m4v", "avi", "unknown"]


def _require_deps() -> tuple[Any, Any, Any, Any]:
    """Import optional dependencies only when needed."""
    try:
        import requests  # type: ignore
        from ddgs import DDGS  # type: ignore
        from PIL import Image, ImageOps  # type: ignore
    except ModuleNotFoundError as e:
        missing = getattr(e, "name", None) or "a required dependency"
        print(
            "Missing dependency for media download script.\n"
            f"  Missing: {missing}\n"
            '  Install: pip install -e ".[images]"  (or: pip install ddgs Pillow requests)',
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
            person_name,
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


def _require_ocr_deps() -> tuple[Any, Any]:
    """Import OCR dependencies (cv2, easyocr) only when needed."""
    try:
        import cv2  # type: ignore
        import easyocr  # type: ignore
        return cv2, easyocr
    except ModuleNotFoundError as e:
        missing = getattr(e, "name", None) or "a required dependency"
        print(
            "Missing dependency for text detection.\n"
            f"  Missing: {missing}\n"
            '  Install: pip install -e ".[images]"  (or: pip install opencv-python easyocr)',
            file=sys.stderr,
        )
        raise SystemExit(2) from e


# Global OCR reader (lazy init to avoid slow startup)
_ocr_reader: Any = None


def _get_ocr_reader() -> Any:
    """Get or create EasyOCR reader (cached globally)."""
    global _ocr_reader
    if _ocr_reader is None:
        _, easyocr = _require_ocr_deps()
        print("Initializing OCR reader (first time may take a moment)...")
        _ocr_reader = easyocr.Reader(["en", "es"], gpu=False, verbose=False)
    return _ocr_reader


def _extract_video_frames(video_path: Path, num_frames: int = 4) -> list[Any]:
    """Extract evenly-spaced frames from a video file."""
    cv2, _ = _require_ocr_deps()
    frames = []
    cap = cv2.VideoCapture(str(video_path))
    try:
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            return []
        # Sample at 20%, 40%, 60%, 80% of video
        positions = [int(total_frames * p) for p in [0.2, 0.4, 0.6, 0.8]][:num_frames]
        for pos in positions:
            cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
            ret, frame = cap.read()
            if ret and frame is not None:
                frames.append(frame)
    finally:
        cap.release()
    return frames


def _video_has_text_overlay(
    video_path: Path,
    *,
    min_chars: int = 15,
    num_frames: int = 4,
    verbose: bool = False,
) -> bool:
    """Check if a video has significant text overlay using OCR.
    
    Returns True if detected text exceeds min_chars in any frame.
    """
    frames = _extract_video_frames(video_path, num_frames=num_frames)
    if not frames:
        return False  # Can't check, assume OK
    
    reader = _get_ocr_reader()
    
    for i, frame in enumerate(frames):
        try:
            # EasyOCR returns list of (bbox, text, confidence)
            results = reader.readtext(frame, detail=1, paragraph=False)
            total_text = "".join(r[1] for r in results if len(r) >= 2)
            char_count = len(total_text.strip())
            if verbose:
                print(f"  Frame {i+1}: detected {char_count} chars")
            if char_count >= min_chars:
                return True
        except Exception:
            continue
    
    return False


def _get_video_orientation(video_path: Path) -> Orientation | None:
    """Get video orientation (horizontal/vertical) from its dimensions.
    
    Returns None if unable to determine.
    """
    cv2, _ = _require_ocr_deps()
    cap = cv2.VideoCapture(str(video_path))
    try:
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if width <= 0 or height <= 0:
            return None
        if width == height:
            return None  # Square, doesn't match either
        return "horizontal" if width > height else "vertical"
    finally:
        cap.release()


def _video_matches_orientation(video_path: Path, orientation: Orientation) -> bool:
    """Check if video matches the desired orientation."""
    if orientation == "any":
        return True
    actual = _get_video_orientation(video_path)
    if actual is None:
        return False  # Can't determine, reject
    return actual == orientation


# Video source priority (lower = higher priority)
_SOURCE_PRIORITY: dict[str, int] = {
    "youtube": 1,
    "vimeo": 2,
    "dailymotion": 2,
    "facebook": 2,
    "twitter": 2,
    "other": 3,
    "instagram": 4,
    "tiktok": 5,
}


def _get_video_source(url: str) -> str:
    """Identify video source from URL."""
    u = url.lower()
    if "youtube.com" in u or "youtu.be" in u:
        return "youtube"
    if "tiktok.com" in u:
        return "tiktok"
    if "instagram.com" in u:
        return "instagram"
    if "vimeo.com" in u:
        return "vimeo"
    if "dailymotion.com" in u:
        return "dailymotion"
    if "facebook.com" in u or "fb.watch" in u:
        return "facebook"
    if "twitter.com" in u or "x.com" in u:
        return "twitter"
    return "other"


def _sort_urls_by_source_priority(urls: list[str]) -> list[str]:
    """Sort URLs by source priority (YouTube first, TikTok/Instagram last)."""
    return sorted(urls, key=lambda u: _SOURCE_PRIORITY.get(_get_video_source(u), 6))


def download_person_videos(
    person_name: str,
    num_videos: int,
    out_dir: Path,
    *,
    orientation: Orientation = "any",
    max_results: int = 50,
    region: str = "wt-wt",
    safesearch: str = "moderate",
    max_duration_sec: int = 180,
    skip_text_videos: bool = False,
    text_min_chars: int = 15,
    verbose: bool = False,
) -> int:
    """Download short videos for a person using DuckDuckGo video search + yt-dlp.

    Searches DuckDuckGo for video URLs (YouTube, TikTok, etc.) and uses yt-dlp
    to download them. "Short" is enforced via max_duration_sec (default 60s).
    
    If orientation is set, only videos matching that orientation are kept.
    If skip_text_videos=True, videos with text overlays (detected via OCR) are
    deleted and replaced with the next candidate.
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
    video_index = 0  # For naming files sequentially
    seen_urls: set[str] = set()

    query = f"{person_name} short video"

    # Collect video URLs from DuckDuckGo
    video_urls: list[str] = []
    with DDGS() as ddgs:
        results = ddgs.videos(
            query,
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

    # Sort by source priority (YouTube first, TikTok/Instagram last)
    video_urls = _sort_urls_by_source_priority(video_urls)

    # Count sources for info message
    source_counts = Counter(_get_video_source(u) for u in video_urls)
    sources_info = ", ".join(f"{src}:{cnt}" for src, cnt in source_counts.most_common())

    filters = []
    if orientation != "any":
        filters.append(f"orientation={orientation}")
    if skip_text_videos:
        filters.append("no text overlays")
    filter_msg = f" ({', '.join(filters)})" if filters else ""
    print(f"Found {len(video_urls)} video URLs [{sources_info}]")
    print(f"Downloading up to {num_videos} videos (max {max_duration_sec}s){filter_msg}...")

    for url in video_urls:
        if downloaded >= num_videos:
            break

        video_index += 1
        out_filename = f"{_slugify_folder(person_name)}_{video_index:03}.mp4"
        out_path = folder / out_filename

        # yt-dlp options (per-video to control output filename)
        ydl_opts = {
            "format": "best[ext=mp4]/best",
            "outtmpl": str(out_path.with_suffix(".%(ext)s")),
            "quiet": not verbose,
            "no_warnings": not verbose,
            "ignoreerrors": True,
            "noplaylist": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info first to check duration
                info = ydl.extract_info(url, download=False)
                if info is None:
                    if verbose:
                        print(f"Skip video: {url} (could not extract info)")
                    video_index -= 1  # Reuse index
                    continue

                duration = info.get("duration") or 0
                if duration > max_duration_sec:
                    if verbose:
                        print(f"Skip video: {url} (duration {duration}s > {max_duration_sec}s)")
                    video_index -= 1
                    continue

                # Download the video
                ydl.download([url])

            # Find the actual downloaded file (extension might vary)
            downloaded_files = list(folder.glob(f"{_slugify_folder(person_name)}_{video_index:03}.*"))
            if not downloaded_files:
                if verbose:
                    print(f"Skip video: {url} (download failed)")
                video_index -= 1
                continue

            actual_path = downloaded_files[0]

            # Check orientation if specified
            if orientation != "any":
                if not _video_matches_orientation(actual_path, orientation):
                    actual_orient = _get_video_orientation(actual_path) or "unknown"
                    print(f"Rejected (orientation {actual_orient}, need {orientation}): {actual_path.name}")
                    actual_path.unlink()
                    video_index -= 1
                    continue

            # Check for text overlay if enabled
            if skip_text_videos:
                if verbose:
                    print(f"Checking for text overlay: {actual_path.name}")
                has_text = _video_has_text_overlay(
                    actual_path,
                    min_chars=text_min_chars,
                    verbose=verbose,
                )
                if has_text:
                    print(f"Rejected (text detected): {actual_path.name}")
                    actual_path.unlink()  # Delete the video
                    video_index -= 1
                    continue

            downloaded += 1
            title = info.get("title", url)[:50]
            print(f"Saved video {downloaded}: {actual_path.name} ({title})")

        except Exception as e:
            if verbose:
                print(f"Skip video: {url} ({type(e).__name__}: {e})")
            video_index -= 1
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
        "--video-orientation",
        choices=["horizontal", "vertical", "any"],
        default="any",
        help="Filter videos by orientation (default: any = no filter).",
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
        default=180,
        metavar="SECS",
        help="Max video duration in seconds (default: 180 = 3 min). Videos longer than this are skipped.",
    )
    parser.add_argument(
        "--skip-text-videos",
        action="store_true",
        help="Use OCR to detect and skip videos with text overlays (TikTok captions, etc.).",
    )
    parser.add_argument(
        "--text-min-chars",
        type=int,
        default=15,
        metavar="N",
        help="Minimum characters to consider as 'has text overlay' (default: 15).",
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
            orientation=args.video_orientation,  # type: ignore[arg-type]
            max_results=args.video_max_results,
            region=args.region,
            safesearch=args.safesearch,
            max_duration_sec=args.max_video_duration,
            skip_text_videos=args.skip_text_videos,
            text_min_chars=args.text_min_chars,
            verbose=args.verbose,
        )

    raise SystemExit(max(exit_code_img, exit_code_vid))


if __name__ == "__main__":
    main()

