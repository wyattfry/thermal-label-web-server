import os

APP_DIR = r"C:\label-upload"
UPLOAD_DIR = os.path.join(APP_DIR, "uploads")
LOG_DIR = os.path.join(APP_DIR, "logs")
SUMATRA = r"C:\Users\wyatt\AppData\Local\SumatraPDF\SumatraPDF.exe"
PRINTER = r"4BARCODE 4B-2054L"
ALLOWED_EXT = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".gif"}
PRINT_SETTINGS = "fit,portrait,paper=4x6"
LABEL_DPI = 203
LABEL_SIZE_IN = (4, 6)
AUTO_DETECT_DPI = 150
