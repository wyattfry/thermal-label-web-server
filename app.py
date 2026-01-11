from flask import Flask, request, redirect, url_for, render_template_string, send_from_directory
import os
import pathlib
import subprocess
import time
from urllib.parse import quote
import socket
import traceback
from typing import Optional

APP_DIR = r"C:\\label-upload"
UPLOAD_DIR = os.path.join(APP_DIR, "uploads")
LOG_DIR = os.path.join(APP_DIR, "logs")
SUMATRA = r"C:\\Users\\wyatt\\AppData\\Local\\SumatraPDF\\SumatraPDF.exe"
PRINTER = r"4BARCODE 4B-2054L"
ALLOWED_EXT = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".gif"}
PRINT_SETTINGS = "fit,portrait,paper=4x6"
LABEL_DPI = 203
LABEL_SIZE_IN = (4, 6)
AUTO_DETECT_DPI = 150

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

app = Flask(__name__)

PAGE = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Thermal Label Printer</title>
    <style>
      body { font-family: sans-serif; margin: 24px; }
      .box { max-width: 520px; }
      form { display: grid; gap: 16px; }
      label { font-size: 14px; color: #333; }
      input[type=file], select, button { width: 100%; font-size: 16px; }
      input[type=file] { padding: 6px 0; }
      select { padding: 8px 10px; }
      button { padding: 12px 14px; }
      .status { margin-top: 16px; padding: 10px; background: #f4f4f4; }
      .actions { display: grid; gap: 10px; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); }
      .checkbox { display: flex; align-items: center; gap: 8px; font-size: 14px; }
      .checkbox input { width: auto; }
    </style>
  </head>
  <body>
    <div class="box">
      <h2>Thermal Label Printer</h2>
      <p>Supported formats: PDF, PNG, JPG, JPEG, TIFF, BMP, GIF</p>
      <p>Multi-page PDFs print one page per label. Image options apply to images and PDFs.</p>
      <p>PDF crop/rotate requires PyMuPDF (pip install pymupdf).</p>
      <p>If PDF processing fails, check logs in C:\\label-upload\\logs.</p>
      <form method="post" action="/print" enctype="multipart/form-data">
        <div>
          <label for="file">Choose file</label>
          <input id="file" type="file" name="file" required />
        </div>
        <div>
          <label for="mode">Image mode</label>
          <select id="mode" name="mode">
            <option value="auto_detect" selected>Auto detect (crop label, auto-rotate)</option>
            <option value="crop_center">Crop center to fill 4x6</option>
            <option value="crop_top">Crop top (label near top)</option>
            <option value="stretch">Stretch to fill 4x6</option>
            <option value="fit">Fit with margins</option>
          </select>
        </div>
        <div>
          <label for="rotate">Rotate</label>
          <select id="rotate" name="rotate">
            <option value="0">0 deg</option>
            <option value="90">90 deg</option>
            <option value="180">180 deg</option>
            <option value="270">270 deg</option>
          </select>
        </div>
        <div class="checkbox">
          <input id="debug" type="checkbox" name="debug" value="1" />
          <label for="debug">Save auto-detect debug images</label>
        </div>
        <div class="actions">
          <button type="submit" name="action" value="print">Print</button>
          <button type="submit" name="action" value="preview">Preview</button>
        </div>
      </form>
      {% if message %}
      <div class="status">{{ message }}</div>
      {% endif %}
    </div>
  </body>
</html>
"""

PREVIEW_PAGE = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Print Preview</title>
    <style>
      body { font-family: sans-serif; margin: 24px; }
      .box { max-width: 860px; }
      .preview-grid { display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); }
      .label { width: 100%; aspect-ratio: 2 / 3; background: #fff; border: 1px solid #ddd; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08); display: flex; align-items: center; justify-content: center; }
      .label img { max-width: 100%; max-height: 100%; object-fit: contain; }
      .actions { display: grid; gap: 10px; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); margin-top: 16px; }
      button { padding: 12px 14px; font-size: 16px; }
      .actions a { display: inline-block; padding: 12px 14px; background: #eee; color: #222; text-decoration: none; text-align: center; }
      .file-actions { display: flex; gap: 8px; justify-content: center; margin-top: 8px; }
      .file-actions a { padding: 6px 10px; background: #f2f2f2; color: #222; text-decoration: none; font-size: 13px; border-radius: 4px; }
      .debug { margin-top: 6px; font-size: 12px; color: #555; text-align: center; display: flex; flex-wrap: wrap; gap: 6px; justify-content: center; }
      .debug a { color: #333; text-decoration: none; background: #f6f6f6; padding: 4px 6px; border-radius: 4px; }
    </style>
  </head>
  <body>
    <div class="box">
      <h2>Print Preview</h2>
      <p>Rendered at 4x6. If it looks correct, click Print.</p>
      <div class="preview-grid">
        {% for f in files %}
          <div>
            <div class="label">
              <img src="{{ url_for('files', filename=f) }}" alt="Preview {{ loop.index }}" />
            </div>
            <div class="file-actions">
              <a href="{{ url_for('edit_file', filename=f) }}">Edit crop/rotate</a>
            </div>
            {% if debug_files.get(f) %}
              <div class="debug">
                {% for d in debug_files.get(f) %}
                  <a href="{{ url_for('files', filename=d) }}">{{ d }}</a>
                {% endfor %}
              </div>
            {% endif %}
          </div>
        {% endfor %}
      </div>
      <form method="post" action="/print-processed" class="actions">
        {% for f in files %}
        <input type="hidden" name="files" value="{{ f }}" />
        {% endfor %}
        <button type="submit">Print</button>
        <a href="/">Back</a>
      </form>
    </div>
  </body>
</html>
"""

EDIT_PAGE = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Edit Label</title>
    <style>
      body { font-family: sans-serif; margin: 24px; }
      .box { max-width: 960px; }
      .toolbar { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-bottom: 12px; }
      button { padding: 10px 12px; font-size: 14px; }
      canvas { border: 1px solid #ddd; background: #fff; width: 100%; height: auto; }
      .hint { font-size: 13px; color: #555; margin-top: 8px; }
      .actions { display: grid; gap: 10px; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); margin-top: 16px; }
      .actions a { display: inline-block; padding: 12px 14px; background: #eee; color: #222; text-decoration: none; text-align: center; }
    </style>
  </head>
  <body>
    <div class="box">
      <h2>Edit Crop / Rotate</h2>
      <div class="toolbar">
        <button type="button" id="rotateLeft">Rotate Left</button>
        <button type="button" id="rotateRight">Rotate Right</button>
        <button type="button" id="resetCrop">Reset Crop</button>
      </div>
      <canvas id="canvas"></canvas>
      <div class="hint">Drag to draw a crop box. Rotation applies before crop.</div>
      <form method="post" action="/apply-edit" class="actions">
        <input type="hidden" name="filename" value="{{ filename }}" />
        <input type="hidden" name="rotation" id="rotation" value="0" />
        <input type="hidden" name="crop_x" id="crop_x" value="0" />
        <input type="hidden" name="crop_y" id="crop_y" value="0" />
        <input type="hidden" name="crop_w" id="crop_w" value="0" />
        <input type="hidden" name="crop_h" id="crop_h" value="0" />
        <button type="submit" id="apply">Apply & Preview</button>
        <a href="/">Back</a>
      </form>
    </div>
    <script>
      const img = new Image();
      img.src = "{{ url_for('files', filename=filename) }}";
      const canvas = document.getElementById('canvas');
      const ctx = canvas.getContext('2d');
      let rotation = 0;
      let scale = 1;
      let crop = null;
      let isDragging = false;
      let startX = 0;
      let startY = 0;

      function rotatedDims() {
        if (rotation % 180 === 0) {
          return { w: img.naturalWidth, h: img.naturalHeight };
        }
        return { w: img.naturalHeight, h: img.naturalWidth };
      }

      function resizeCanvas() {
        const dims = rotatedDims();
        const maxW = Math.min(820, document.body.clientWidth - 48);
        scale = Math.min(1, maxW / dims.w);
        canvas.width = Math.round(dims.w * scale);
        canvas.height = Math.round(dims.h * scale);
        if (!crop) {
          crop = { x: 0, y: 0, w: canvas.width, h: canvas.height };
        }
      }

      function draw() {
        if (!img.naturalWidth) {
          return;
        }
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.save();
        ctx.translate(canvas.width / 2, canvas.height / 2);
        ctx.rotate((rotation * Math.PI) / 180);
        ctx.scale(scale, scale);
        ctx.drawImage(img, -img.naturalWidth / 2, -img.naturalHeight / 2);
        ctx.restore();

        if (crop) {
          ctx.save();
          ctx.strokeStyle = '#ff5a5a';
          ctx.lineWidth = 2;
          ctx.strokeRect(crop.x, crop.y, crop.w, crop.h);
          ctx.restore();
        }
      }

      function setHiddenFields() {
        if (!crop) {
          return;
        }
        document.getElementById('rotation').value = rotation;
        document.getElementById('crop_x').value = Math.round(crop.x / scale);
        document.getElementById('crop_y').value = Math.round(crop.y / scale);
        document.getElementById('crop_w').value = Math.round(crop.w / scale);
        document.getElementById('crop_h').value = Math.round(crop.h / scale);
      }

      canvas.addEventListener('mousedown', (e) => {
        const rect = canvas.getBoundingClientRect();
        startX = e.clientX - rect.left;
        startY = e.clientY - rect.top;
        isDragging = true;
        crop = { x: startX, y: startY, w: 0, h: 0 };
      });

      canvas.addEventListener('mousemove', (e) => {
        if (!isDragging) {
          return;
        }
        const rect = canvas.getBoundingClientRect();
        const currentX = e.clientX - rect.left;
        const currentY = e.clientY - rect.top;
        crop.x = Math.min(startX, currentX);
        crop.y = Math.min(startY, currentY);
        crop.w = Math.abs(currentX - startX);
        crop.h = Math.abs(currentY - startY);
        draw();
      });

      window.addEventListener('mouseup', () => {
        if (isDragging) {
          isDragging = false;
          if (crop && (crop.w < 5 || crop.h < 5)) {
            crop = { x: 0, y: 0, w: canvas.width, h: canvas.height };
          }
          setHiddenFields();
          draw();
        }
      });

      document.getElementById('rotateLeft').addEventListener('click', () => {
        rotation = (rotation + 270) % 360;
        resizeCanvas();
        crop = { x: 0, y: 0, w: canvas.width, h: canvas.height };
        setHiddenFields();
        draw();
      });

      document.getElementById('rotateRight').addEventListener('click', () => {
        rotation = (rotation + 90) % 360;
        resizeCanvas();
        crop = { x: 0, y: 0, w: canvas.width, h: canvas.height };
        setHiddenFields();
        draw();
      });

      document.getElementById('resetCrop').addEventListener('click', () => {
        crop = { x: 0, y: 0, w: canvas.width, h: canvas.height };
        setHiddenFields();
        draw();
      });

      img.onload = () => {
        resizeCanvas();
        setHiddenFields();
        draw();
      };

      window.addEventListener('resize', () => {
        resizeCanvas();
        setHiddenFields();
        draw();
      });
    </script>
  </body>
</html>
"""


def _safe_name(name: str) -> str:
    base = os.path.basename(name)
    keep = "-_.() "
    cleaned = "".join(c for c in base if c.isalnum() or c in keep).strip()
    return cleaned or "upload"


def _allowed(path: str) -> bool:
    return pathlib.Path(path).suffix.lower() in ALLOWED_EXT


@app.route("/")
def index():
    msg = request.args.get("msg")
    return render_template_string(PAGE, message=msg)


def _crop_to_label(img, target_w: int, target_h: int, anchor: str, resample):
    target_ratio = target_w / target_h
    src_ratio = img.width / img.height
    if src_ratio > target_ratio:
        new_w = int(img.height * target_ratio)
        left = (img.width - new_w) // 2
        box = (left, 0, left + new_w, img.height)
    else:
        new_h = int(img.width / target_ratio)
        top = 0 if anchor == "top" else (img.height - new_h) // 2
        box = (0, top, img.width, top + new_h)
    img = img.crop(box)
    return img.resize((target_w, target_h), resample)


def _finalize_label_image(img, resample):
    try:
        from PIL import Image
    except Exception:
        return img
    target_w = int(LABEL_SIZE_IN[0] * LABEL_DPI)
    target_h = int(LABEL_SIZE_IN[1] * LABEL_DPI)
    target_ratio = target_w / target_h
    src_ratio = img.width / img.height
    if abs(src_ratio - target_ratio) <= 0.05:
        return img.resize((target_w, target_h), resample)
    img.thumbnail((target_w, target_h), resample)
    canvas = Image.new("RGB", (target_w, target_h), (255, 255, 255))
    x = (target_w - img.width) // 2
    y = (target_h - img.height) // 2
    canvas.paste(img, (x, y))
    return canvas


def _auto_detect_label(img, target_w: int, target_h: int, resample, debug_base: Optional[str]):
    gray = img.convert("L")
    bw = gray.point(lambda p: 255 if p < 240 else 0)
    bbox = bw.getbbox()
    if debug_base:
        try:
            from PIL import ImageDraw
            img.save(debug_base + "_debug_raw.png", "PNG")
            bw.save(debug_base + "_debug_bw.png", "PNG")
            if bbox:
                preview = img.copy()
                draw = ImageDraw.Draw(preview)
                stroke = max(1, img.width // 300)
                draw.rectangle(bbox, outline="red", width=stroke)
                preview.save(debug_base + "_debug_bbox.png", "PNG")
        except Exception:
            pass
    if bbox:
        img = img.crop(bbox)
    if img.width > img.height:
        img = img.rotate(90, expand=True)
    return _crop_to_label(img, target_w, target_h, "center", resample)


def _process_image(path: str, mode: str, rotate: int, debug: bool) -> str:
    try:
        from PIL import Image
    except Exception:
        return path

    ext = pathlib.Path(path).suffix.lower()
    if ext not in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".gif"}:
        return path

    target_w = int(LABEL_SIZE_IN[0] * LABEL_DPI)
    target_h = int(LABEL_SIZE_IN[1] * LABEL_DPI)
    out_path = os.path.splitext(path)[0] + "_processed.png"
    debug_base = os.path.splitext(out_path)[0] if debug and mode == "auto_detect" else None

    with Image.open(path) as img:
        img = img.convert("RGB")
        if rotate:
            img = img.rotate(-rotate, expand=True)

        if mode == "auto_detect":
            img = _auto_detect_label(img, target_w, target_h, Image.LANCZOS, debug_base)
        elif mode == "fit":
            img.thumbnail((target_w, target_h), Image.LANCZOS)
            canvas = Image.new("RGB", (target_w, target_h), (255, 255, 255))
            x = (target_w - img.width) // 2
            y = (target_h - img.height) // 2
            canvas.paste(img, (x, y))
            img = canvas
        elif mode == "stretch":
            img = img.resize((target_w, target_h), Image.LANCZOS)
        else:
            anchor = "top" if mode == "crop_top" else "center"
            img = _crop_to_label(img, target_w, target_h, anchor, Image.LANCZOS)

        img.save(out_path, "PNG", dpi=(LABEL_DPI, LABEL_DPI))

    return out_path


def _pdf_label_clip(page_rect, mode: str):
    label_w = LABEL_SIZE_IN[0] * 72
    label_h = LABEL_SIZE_IN[1] * 72
    if page_rect.width < label_w or page_rect.height < label_h:
        return None
    left = (page_rect.width - label_w) / 2
    if mode == "crop_top":
        top = page_rect.y0
    else:
        top = (page_rect.height - label_h) / 2
    return (left, top, left + label_w, top + label_h)


def _process_pdf(path: str, mode: str, rotate: int, debug: bool) -> list[str]:
    try:
        import pymupdf as fitz
    except Exception as exc:
        _log_error(f"PyMuPDF import failed: {exc}")
        return []

    out_paths: list[str] = []
    try:
        doc = fitz.open(path)
    except Exception as exc:
        _log_error(f"PyMuPDF open failed: {exc}")
        return []

    for idx in range(doc.page_count):
        page = doc.load_page(idx)
        clip = None
        if mode in {"crop_center", "crop_top"}:
            clip = _pdf_label_clip(page.rect, mode)
        if clip:
            pix = page.get_pixmap(dpi=LABEL_DPI, clip=fitz.Rect(clip))
            image_mode = "fit"
        else:
            dpi = AUTO_DETECT_DPI if mode == "auto_detect" else LABEL_DPI
            pix = page.get_pixmap(dpi=dpi)
            image_mode = mode
        page_path = os.path.splitext(path)[0] + f"_page{idx+1}.png"
        pix.save(page_path)
        processed = _process_image(page_path, image_mode, rotate, debug)
        out_paths.append(processed)

    return out_paths


def _log_error(message: str) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    log_path = os.path.join(LOG_DIR, "label-upload.log")
    print(f"[{ts}] {message}")
    traceback.print_exc()
    with open(log_path, "a", encoding="ascii", errors="replace") as handle:
        handle.write(f"[{ts}] {message}\n")
        handle.write(traceback.format_exc())
        handle.write("\n")


def _send_to_printer(paths: list[str]) -> Optional[str]:
    try:
        for print_path in paths:
            subprocess.run(
                [
                    SUMATRA,
                    "-silent",
                    "-print-to",
                    PRINTER,
                    "-print-settings",
                    PRINT_SETTINGS,
                    print_path,
                ],
                check=True,
                timeout=120,
            )
    except subprocess.TimeoutExpired:
        return "Print timed out"
    except subprocess.CalledProcessError as exc:
        return f"Print failed: {exc}"
    return None


def _resolve_uploaded_files(names: list[str]) -> list[str]:
    paths = []
    for name in names:
        base = os.path.basename(name)
        if not base:
            continue
        path = os.path.join(UPLOAD_DIR, base)
        if os.path.isfile(path):
            paths.append(path)
    return paths


def _debug_files_for(processed: list[str]) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}
    for path in processed:
        if not path:
            continue
        base = os.path.splitext(path)[0]
        candidates = [
            base + "_debug_raw.png",
            base + "_debug_bw.png",
            base + "_debug_bbox.png",
        ]
        existing = [os.path.basename(p) for p in candidates if os.path.exists(p)]
        if existing:
            mapping[os.path.basename(path)] = existing
    return mapping


@app.errorhandler(Exception)
def handle_exception(exc):
    _log_error(f"Unhandled error: {exc}")
    return render_template_string(PAGE, message="Internal error. Check logs."), 500


@app.route("/print", methods=["POST"])
def print_file():
    if "file" not in request.files:
        return render_template_string(PAGE, message="No file uploaded")

    f = request.files["file"]
    if not f.filename:
        return render_template_string(PAGE, message="Missing filename")

    safe = _safe_name(f.filename)
    if not _allowed(safe):
        return render_template_string(PAGE, message="Unsupported file type")

    ts = time.strftime("%Y%m%d-%H%M%S")
    out_name = f"{ts}-{safe}"
    out_path = os.path.join(UPLOAD_DIR, out_name)
    f.save(out_path)

    if not os.path.exists(SUMATRA):
        return render_template_string(PAGE, message="SumatraPDF not found")

    mode = request.form.get("mode", "auto_detect")
    rotate = request.form.get("rotate", "0")
    action = request.form.get("action", "print")
    debug = request.form.get("debug") == "1"
    try:
        rotate = int(rotate)
    except ValueError:
        rotate = 0

    ext = pathlib.Path(out_path).suffix.lower()
    pdf_paths: list[str] = []
    print_path = None
    if ext == ".pdf":
        pdf_paths = _process_pdf(out_path, mode, rotate, debug)
        if not pdf_paths:
            return render_template_string(
                PAGE, message="PDF processing requires PyMuPDF (pip install pymupdf)"
            )
    else:
        print_path = _process_image(out_path, mode, rotate, debug)
        if print_path != out_path and not os.path.exists(print_path):
            print_path = out_path

    if pdf_paths:
        print_paths = pdf_paths
    else:
        print_paths = [print_path] if print_path else []

    if action == "preview":
        preview_files = [os.path.basename(p) for p in print_paths if p]
        if not preview_files:
            return render_template_string(PAGE, message="Nothing to preview")
        debug_files = _debug_files_for(print_paths)
        return render_template_string(PREVIEW_PAGE, files=preview_files, debug_files=debug_files)

    error = _send_to_printer(print_paths)
    if error:
        return render_template_string(PAGE, message=error)

    msg = quote("Print submitted")
    return redirect(url_for("index") + f"?msg={msg}")


@app.route("/print-processed", methods=["POST"])
def print_processed():
    files = request.form.getlist("files")
    paths = _resolve_uploaded_files(files)
    if not paths:
        return render_template_string(PAGE, message="Nothing to print")
    error = _send_to_printer(paths)
    if error:
        return render_template_string(PAGE, message=error)
    msg = quote("Print submitted")
    return redirect(url_for("index") + f"?msg={msg}")


@app.route("/edit/<path:filename>")
def edit_file(filename):
    safe = os.path.basename(filename)
    path = os.path.join(UPLOAD_DIR, safe)
    if not os.path.isfile(path):
        return render_template_string(PAGE, message="File not found")
    return render_template_string(EDIT_PAGE, filename=safe)


@app.route("/apply-edit", methods=["POST"])
def apply_edit():
    try:
        from PIL import Image
    except Exception:
        return render_template_string(PAGE, message="Pillow is required for editing")

    filename = request.form.get("filename", "")
    safe = os.path.basename(filename)
    path = os.path.join(UPLOAD_DIR, safe)
    if not os.path.isfile(path):
        return render_template_string(PAGE, message="File not found")

    try:
        rotation = int(request.form.get("rotation", "0"))
        crop_x = int(request.form.get("crop_x", "0"))
        crop_y = int(request.form.get("crop_y", "0"))
        crop_w = int(request.form.get("crop_w", "0"))
        crop_h = int(request.form.get("crop_h", "0"))
    except ValueError:
        rotation = 0
        crop_x = crop_y = crop_w = crop_h = 0

    out_path = os.path.splitext(path)[0] + "_edited.png"

    with Image.open(path) as img:
        img = img.convert("RGB")
        if rotation:
            img = img.rotate(-rotation, expand=True)
        if crop_w > 0 and crop_h > 0:
            left = max(0, crop_x)
            top = max(0, crop_y)
            right = min(img.width, left + crop_w)
            bottom = min(img.height, top + crop_h)
            if right > left and bottom > top:
                img = img.crop((left, top, right, bottom))
        img = _finalize_label_image(img, Image.LANCZOS)
        img.save(out_path, "PNG", dpi=(LABEL_DPI, LABEL_DPI))

    preview_files = [os.path.basename(out_path)]
    return render_template_string(PREVIEW_PAGE, files=preview_files, debug_files={})


@app.route("/files/<path:filename>")
def files(filename):
    return send_from_directory(UPLOAD_DIR, filename)


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    host = "0.0.0.0"
    port = 8088
    print(f"Starting label uploader from {__file__} (pid {os.getpid()})")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(0.5)
        if probe.connect_ex(("127.0.0.1", port)) == 0:
            raise SystemExit(f"Port {port} is already in use.")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except OSError:
            raise SystemExit(f"Port {port} is already in use.")
    app.run(host=host, port=port, use_reloader=False)
