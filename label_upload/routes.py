import os
import pathlib
import time
from urllib.parse import quote

from flask import redirect, render_template, request, send_from_directory, url_for

from .printing import send_to_printer
from .processing import debug_files_for, finalize_label_image, process_image, process_pdf
from .settings import LABEL_DPI, SUMATRA, UPLOAD_DIR
from .utils import allowed, log_error, resolve_uploaded_files, safe_name


def register_routes(app):
    @app.route("/")
    def index():
        msg = request.args.get("msg")
        return render_template("index.html", message=msg)

    @app.errorhandler(Exception)
    def handle_exception(exc):
        log_error(f"Unhandled error: {exc}")
        return render_template("index.html", message="Internal error. Check logs."), 500

    @app.route("/print", methods=["POST"])
    def print_file():
        if "file" not in request.files:
            return render_template("index.html", message="No file uploaded")

        f = request.files["file"]
        if not f.filename:
            return render_template("index.html", message="Missing filename")

        safe = safe_name(f.filename)
        if not allowed(safe):
            return render_template("index.html", message="Unsupported file type")

        ts = time.strftime("%Y%m%d-%H%M%S")
        out_name = f"{ts}-{safe}"
        out_path = os.path.join(UPLOAD_DIR, out_name)
        f.save(out_path)

        if not os.path.exists(SUMATRA):
            return render_template("index.html", message="SumatraPDF not found")

        mode = request.form.get("mode", "auto_detect")
        rotate = request.form.get("rotate", "0")
        action = request.form.get("action", "print")
        debug = request.form.get("debug") == "1"
        try:
            rotate = int(rotate)
        except ValueError:
            rotate = 0

        ext = pathlib.Path(out_path).suffix.lower()
        pdf_paths = []
        print_path = None
        if ext == ".pdf":
            pdf_paths = process_pdf(out_path, mode, rotate, debug)
            if not pdf_paths:
                return render_template(
                    "index.html", message="PDF processing requires PyMuPDF (pip install pymupdf)"
                )
        else:
            print_path = process_image(out_path, mode, rotate, debug)
            if print_path != out_path and not os.path.exists(print_path):
                print_path = out_path

        if pdf_paths:
            print_paths = pdf_paths
        else:
            print_paths = [print_path] if print_path else []

        if action == "preview":
            preview_files = [os.path.basename(p) for p in print_paths if p]
            if not preview_files:
                return render_template("index.html", message="Nothing to preview")
            debug_files = debug_files_for(print_paths)
            return render_template("preview.html", files=preview_files, debug_files=debug_files)

        error = send_to_printer(print_paths)
        if error:
            return render_template("index.html", message=error)

        msg = quote("Print submitted")
        return redirect(url_for("index") + f"?msg={msg}")

    @app.route("/print-processed", methods=["POST"])
    def print_processed():
        files = request.form.getlist("files")
        paths = resolve_uploaded_files(files)
        if not paths:
            return render_template("index.html", message="Nothing to print")
        error = send_to_printer(paths)
        if error:
            return render_template("index.html", message=error)
        msg = quote("Print submitted")
        return redirect(url_for("index") + f"?msg={msg}")

    @app.route("/edit/<path:filename>")
    def edit_file(filename):
        safe = os.path.basename(filename)
        path = os.path.join(UPLOAD_DIR, safe)
        if not os.path.isfile(path):
            return render_template("index.html", message="File not found")
        return render_template("edit.html", filename=safe)

    @app.route("/apply-edit", methods=["POST"])
    def apply_edit():
        try:
            from PIL import Image
        except Exception:
            return render_template("index.html", message="Pillow is required for editing")

        filename = request.form.get("filename", "")
        safe = os.path.basename(filename)
        path = os.path.join(UPLOAD_DIR, safe)
        if not os.path.isfile(path):
            return render_template("index.html", message="File not found")

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
            img = finalize_label_image(img, Image.LANCZOS)
            img.save(out_path, "PNG", dpi=(LABEL_DPI, LABEL_DPI))

        preview_files = [os.path.basename(out_path)]
        return render_template("preview.html", files=preview_files, debug_files={})

    @app.route("/files/<path:filename>")
    def files(filename):
        return send_from_directory(UPLOAD_DIR, filename)

    @app.route("/health")
    def health():
        return {"status": "ok"}
