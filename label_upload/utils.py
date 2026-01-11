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
