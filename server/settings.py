import os

# Get app directory programmatically (where the server package is located)
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

UPLOAD_DIR = os.path.join(APP_DIR, "uploads")
LOG_DIR = os.path.join(APP_DIR, "logs")

# SumatraPDF executable path - try bundled version first, then check PATH
# Bundled version location (git-ignored directory)
BUNDLED_SUMATRA = os.path.join(APP_DIR, ".sumatrapdf", "SumatraPDF.exe")
# Fallback paths for system-installed SumatraPDF
SYSTEM_SUMATRA_PATHS = [
    os.path.join(os.getenv("LOCALAPPDATA", ""), "SumatraPDF", "SumatraPDF.exe"),
    os.path.join(os.getenv("ProgramFiles", ""), "SumatraPDF", "SumatraPDF.exe"),
    os.path.join(os.getenv("ProgramFiles(x86)", ""), "SumatraPDF", "SumatraPDF.exe"),
]
# Try bundled first, then system paths
SUMATRA = None
if os.path.exists(BUNDLED_SUMATRA):
    SUMATRA = BUNDLED_SUMATRA
else:
    for path in SYSTEM_SUMATRA_PATHS:
        if os.path.exists(path):
            SUMATRA = path
            break

PRINTER = r"4BARCODE 4B-2054L"
ALLOWED_EXT = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".gif"}
PRINT_SETTINGS = "fit,portrait,paper=4x6"
LABEL_DPI = 203
LABEL_SIZE_IN = (4, 6)
AUTO_DETECT_DPI = 150
