"""
SumatraPDF manager: downloads and extracts SumatraPDF on-demand.
This ensures users don't need to install SumatraPDF separately.
"""

import os
import shutil
import urllib.request
import zipfile

SUMATRA_VERSION = "3.5.2"
SUMATRA_DOWNLOAD_URL = f"https://www.sumatrapdfreader.org/dl/rel/{SUMATRA_VERSION}/SumatraPDF-{SUMATRA_VERSION}-64.zip"
SUMATRA_DIR_NAME = ".sumatrapdf"
SUMATRA_EXE_NAME = "SumatraPDF.exe"


def get_bundled_sumatra_path(app_dir: str) -> str:
    """Get the expected path to the bundled SumatraPDF executable."""
    return os.path.join(app_dir, SUMATRA_DIR_NAME, SUMATRA_EXE_NAME)


def is_sumatra_available(app_dir: str) -> bool:
    """Check if SumatraPDF is available (either bundled or from system)."""
    bundled = get_bundled_sumatra_path(app_dir)
    if os.path.exists(bundled):
        return True
    # Check system paths
    system_paths = [
        os.path.join(os.getenv("APPDATA", ""), "Local", "SumatraPDF", SUMATRA_EXE_NAME),
        os.path.join(os.getenv("ProgramFiles", ""), "SumatraPDF", SUMATRA_EXE_NAME),
        os.path.join(os.getenv("ProgramFiles(x86)", ""), "SumatraPDF", SUMATRA_EXE_NAME),
    ]
    return any(os.path.exists(p) for p in system_paths)


def download_sumatra(app_dir: str) -> str:
    """
    Download and extract SumatraPDF to .sumatrapdf/ directory.
    Returns the path to the extracted executable.
    Raises an exception if download or extraction fails.
    """
    sumatra_base = os.path.join(app_dir, SUMATRA_DIR_NAME)
    sumatra_exe = os.path.join(sumatra_base, SUMATRA_EXE_NAME)

    # If already extracted, return
    if os.path.exists(sumatra_exe):
        return sumatra_exe

    # Create temp directory for download
    os.makedirs(sumatra_base, exist_ok=True)
    zip_path = os.path.join(sumatra_base, "SumatraPDF.zip")

    try:
        print(f"Downloading SumatraPDF {SUMATRA_VERSION}...")
        print(f"From: {SUMATRA_DOWNLOAD_URL}")
        urllib.request.urlretrieve(SUMATRA_DOWNLOAD_URL, zip_path)

        print(f"Extracting to {sumatra_base}...")
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(sumatra_base)

        # Clean up zip file
        os.remove(zip_path)

        if not os.path.exists(sumatra_exe):
            raise FileNotFoundError(f"SumatraPDF.exe not found after extraction at {sumatra_exe}")

        print(f"SumatraPDF ready at: {sumatra_exe}")
        return sumatra_exe

    except Exception as e:
        # Clean up on failure
        if os.path.exists(sumatra_base):
            shutil.rmtree(sumatra_base, ignore_errors=True)
        raise RuntimeError(f"Failed to set up SumatraPDF: {e}")


def ensure_sumatra_available(app_dir: str) -> str:
    """
    Ensure SumatraPDF is available, downloading if necessary.
    Returns the path to the SumatraPDF executable.
    Raises an exception if SumatraPDF cannot be obtained.
    """
    bundled = get_bundled_sumatra_path(app_dir)
    if os.path.exists(bundled):
        return bundled

    # Check for system-installed version
    system_paths = [
        os.path.join(os.getenv("APPDATA", ""), "Local", "SumatraPDF", SUMATRA_EXE_NAME),
        os.path.join(os.getenv("ProgramFiles", ""), "SumatraPDF", SUMATRA_EXE_NAME),
        os.path.join(os.getenv("ProgramFiles(x86)", ""), "SumatraPDF", SUMATRA_EXE_NAME),
    ]
    for path in system_paths:
        if os.path.exists(path):
            return path

    # If not found anywhere, download and extract
    return download_sumatra(app_dir)
