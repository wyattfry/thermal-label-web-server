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
DOWNLOAD_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) label-upload/1.0"


def get_system_sumatra_paths() -> list[str]:
    return [
        os.path.join(os.getenv("LOCALAPPDATA", ""), "SumatraPDF", SUMATRA_EXE_NAME),
        os.path.join(os.getenv("ProgramFiles", ""), "SumatraPDF", SUMATRA_EXE_NAME),
        os.path.join(os.getenv("ProgramFiles(x86)", ""), "SumatraPDF", SUMATRA_EXE_NAME),
    ]


def get_bundled_sumatra_path(app_dir: str) -> str:
    """Get the expected path to the bundled SumatraPDF executable."""
    return os.path.join(app_dir, SUMATRA_DIR_NAME, SUMATRA_EXE_NAME)


def is_sumatra_available(app_dir: str) -> bool:
    """Check if SumatraPDF is available (either bundled or from system)."""
    bundled = get_bundled_sumatra_path(app_dir)
    if os.path.exists(bundled):
        return True
    # Check system paths
    return any(os.path.exists(path) for path in get_system_sumatra_paths())


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
        request = urllib.request.Request(
            SUMATRA_DOWNLOAD_URL,
            headers={"User-Agent": DOWNLOAD_USER_AGENT},
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            with open(zip_path, "wb") as handle:
                shutil.copyfileobj(response, handle)

        print(f"Extracting to {sumatra_base}...")
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            executable_names = [
                name
                for name in zip_ref.namelist()
                if os.path.basename(name).lower().startswith("sumatrapdf")
                and name.lower().endswith(".exe")
            ]
            if not executable_names:
                raise FileNotFoundError("SumatraPDF executable not found in archive")
            with zip_ref.open(executable_names[0]) as source:
                with open(sumatra_exe, "wb") as target:
                    shutil.copyfileobj(source, target)

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
    for path in get_system_sumatra_paths():
        if os.path.exists(path):
            return path

    # If not found anywhere, download and extract
    return download_sumatra(app_dir)
