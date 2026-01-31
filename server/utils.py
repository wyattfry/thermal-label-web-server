import os
import pathlib
import time
import traceback
from typing import List

from .settings import ALLOWED_EXT, LOG_DIR, UPLOAD_DIR


def safe_name(name: str) -> str:
    base = os.path.basename(name)
    keep = "-_.() "
    cleaned = "".join(c for c in base if c.isalnum() or c in keep).strip()
    return cleaned or "upload"


def allowed(path: str) -> bool:
    return pathlib.Path(path).suffix.lower() in ALLOWED_EXT


def log_error(message: str) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    log_path = os.path.join(LOG_DIR, "label-upload.log")
    print(f"[{ts}] {message}")
    traceback.print_exc()
    with open(log_path, "a", encoding="ascii", errors="replace") as handle:
        handle.write(f"[{ts}] {message}")
        handle.write(traceback.format_exc())
        handle.write("")


def resolve_uploaded_files(names: List[str]) -> List[str]:
    paths = []
    for name in names:
        base = os.path.basename(name)
        if not base:
            continue
        path = os.path.join(UPLOAD_DIR, base)
        if os.path.isfile(path):
            paths.append(path)
    return paths

def cleanup_files(upload_path: str, processed_paths: list[str]) -> None:
    candidates = set()
    if upload_path:
        candidates.add(upload_path)
    for path in processed_paths or []:
        if not path:
            continue
        candidates.add(path)
        base, ext = os.path.splitext(path)
        if base.endswith("_processed"):
            candidates.add(base[:-10] + ext)
        debug_suffixes = ["_debug_raw.png", "_debug_bw.png", "_debug_bbox.png"]
        for suffix in debug_suffixes:
            candidates.add(base + suffix)
    for path in candidates:
        try:
            if os.path.isfile(path):
                os.remove(path)
        except Exception:
            pass
