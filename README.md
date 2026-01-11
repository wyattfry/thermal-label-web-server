# Thermal Label Printer Web Interface

This Windows Python/Flask app hosts a web page where users can upload files and print 4x6 labels to a USB thermal printer (via SumatraPDF). It includes auto-crop/auto-rotate for PDFs, a preview step, and a manual crop/rotate editor.

## Prerequisites

- Windows 10/11
- Python 3.9+
- SumatraPDF (used for silent printing)
- Microsoft Visual C++ Redistributable (required by some PDF/rendering libraries)

Python packages:
- Flask (required)
- Pillow (required for image processing and manual edit UI)
- PyMuPDF (required for PDF processing)

## Install

1) Install SumatraPDF and note its path.
2) Create and activate a virtual environment (recommended).
3) Install Python dependencies:

```shell
python -m pip install flask pillow pymupdf
```

## Configure

Edit `label_upload/settings.py`:
- `SUMATRA`: full path to `SumatraPDF.exe`
- `PRINTER`: Windows printer name
- `PRINT_SETTINGS`: Sumatra print settings string
- `LABEL_DPI`, `LABEL_SIZE_IN`: label size and DPI

Uploads and logs default to:
- `C:\label-upload\uploads`
- `C:\label-upload\logs`

## Run

```shell
python app.py
```

Open `http://localhost:8088`.

## Notes

- PDFs are rasterized with PyMuPDF; images are processed with Pillow.
- Multi-page PDFs are rendered page-by-page.
- If PDF processing fails, check `C:\label-upload\logs\label-upload.log`.
