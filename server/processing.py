import os
import pathlib
from typing import List, Optional

from .settings import AUTO_DETECT_DPI, LABEL_DPI, LABEL_SIZE_IN
from .utils import log_error


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


def finalize_label_image(img, resample):
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


def process_image(path: str, mode: str, rotate: int, debug: bool) -> str:
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


def process_pdf(path: str, mode: str, rotate: int, debug: bool) -> List[str]:
    try:
        import pymupdf as fitz
    except Exception as exc:
        log_error(f"PyMuPDF import failed: {exc}")
        return []

    out_paths: List[str] = []
    try:
        doc = fitz.open(path)
    except Exception as exc:
        log_error(f"PyMuPDF open failed: {exc}")
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
        processed = process_image(page_path, image_mode, rotate, debug)
        out_paths.append(processed)

    return out_paths


def debug_files_for(processed: List[str]) -> dict:
    mapping: dict = {}
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
