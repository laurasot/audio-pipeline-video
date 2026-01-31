"""List Chrome extensions from a profile on disk. No browser launch."""

import json
from pathlib import Path


def list_profile_extensions(
    user_data_dir: str | Path,
    profile_directory: str,
) -> list[dict[str, str]]:
    """List installed extensions for a Chrome profile by reading the Extensions folder.

    user_data_dir: Chrome "User Data" folder (e.g. .../Chrome Dev/User Data).
    profile_directory: "Default", "Profile 1", "Profile 2", etc.

    Returns list of dicts with keys: extension_id, name, version, description (if present).
    """
    base = Path(user_data_dir).resolve() / profile_directory / "Extensions"
    if not base.is_dir():
        return []

    result: list[dict[str, str]] = []
    for ext_id_dir in base.iterdir():
        if not ext_id_dir.is_dir() or ext_id_dir.name.startswith("."):
            continue
        ext_id = ext_id_dir.name
        # Each extension has version subfolders (e.g. 1.2.3 or long hex)
        version_dirs = [d for d in ext_id_dir.iterdir() if d.is_dir()]
        if not version_dirs:
            continue
        # Prefer a version folder that contains manifest.json
        manifest_path = None
        for vdir in version_dirs:
            mp = vdir / "manifest.json"
            if mp.is_file():
                manifest_path = mp
                break
        if manifest_path is None:
            result.append({"extension_id": ext_id, "name": "(no manifest)", "version": ""})
            continue
        try:
            raw = manifest_path.read_text(encoding="utf-8", errors="replace")
            data = json.loads(raw)
        except (OSError, json.JSONDecodeError):
            result.append({"extension_id": ext_id, "name": "(read error)", "version": ""})
            continue
        name = data.get("name", "")
        if isinstance(name, dict):
            name = name.get("message", str(name))
        if isinstance(name, str) and name.startswith("__MSG_"):
            name = _resolve_message(manifest_path.parent, name)
        version = data.get("version", "")
        description = data.get("description", "")
        if isinstance(description, dict):
            description = description.get("message", str(description))
        if isinstance(description, str) and description.startswith("__MSG_"):
            description = _resolve_message(manifest_path.parent, description)
        result.append({
            "extension_id": ext_id,
            "name": name or ext_id,
            "version": version,
            "description": description or "",
        })
    return sorted(result, key=lambda x: x["name"].lower())


def _resolve_message(ext_root: Path, msg_ref: str) -> str:
    """Resolve __MSG_key__ from _locales/en/messages.json if present."""
    if not msg_ref.startswith("__MSG_") or not msg_ref.endswith("__"):
        return msg_ref
    key = msg_ref[6:-2]
    locales = ext_root / "_locales"
    for lang in ("en", "en_US", "en_GB"):
        path = locales / lang / "messages.json"
        if path.is_file():
            try:
                data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
                obj = data.get(key)
                if isinstance(obj, dict) and "message" in obj:
                    return obj["message"]
            except (OSError, json.JSONDecodeError):
                pass
    return msg_ref
