import os
from dataclasses import dataclass
from typing import Callable, List, Sequence

from .settings import LABEL_DPI, LABEL_SIZE_IN

TEXT_COLOR = (0, 0, 0)
BACKGROUND_COLOR = (255, 255, 255)
HORIZONTAL_MARGIN_RATIO = 0.08
VERTICAL_MARGIN_RATIO = 0.08
LINE_SPACING_RATIO = 0.18
MIN_FONT_SIZE = 12


@dataclass(frozen=True)
class TextLayout:
    lines: Sequence[str]
    font_size: int
    line_height: int
    total_height: int
    max_width: int


def label_pixel_size() -> tuple[int, int]:
    return int(LABEL_SIZE_IN[0] * LABEL_DPI), int(LABEL_SIZE_IN[1] * LABEL_DPI)


def normalize_text(text: str) -> str:
    cleaned = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.strip() for line in cleaned.split("\n")]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


def load_arial_font(size: int):
    from PIL import ImageFont

    font_candidates = [
        os.path.join(os.getenv("WINDIR", r"C:\Windows"), "Fonts", "arial.ttf"),
        "arial.ttf",
        "Arial.ttf",
        "DejaVuSans.ttf",
    ]
    for candidate in font_candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _measure_text(draw, font, text: str) -> tuple[int, int]:
    if not text:
        bbox = draw.textbbox((0, 0), "Ag", font=font)
        return 0, bbox[3] - bbox[1]
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _split_long_token(token: str, max_width: int, draw, font) -> List[str]:
    pieces: List[str] = []
    current = ""
    for char in token:
        probe = f"{current}{char}"
        width, _ = _measure_text(draw, font, probe)
        if current and width > max_width:
            pieces.append(current)
            current = char
        else:
            current = probe
    if current:
        pieces.append(current)
    return pieces or [token]


def wrap_text_lines(text: str, max_width: int, draw, font) -> List[str]:
    wrapped: List[str] = []
    normalized = normalize_text(text)
    paragraphs = normalized.split("\n") if normalized else [""]
    for paragraph in paragraphs:
        if not paragraph:
            wrapped.append("")
            continue
        current = ""
        for token in paragraph.split():
            pieces = _split_long_token(token, max_width, draw, font)
            for piece in pieces:
                candidate = piece if not current else f"{current} {piece}"
                width, _ = _measure_text(draw, font, candidate)
                if current and width > max_width:
                    wrapped.append(current)
                    current = piece
                else:
                    current = candidate
        if current:
            wrapped.append(current)
    return wrapped or [""]


def plan_text_layout(
    text: str,
    canvas_size: tuple[int, int],
    font_loader: Callable[[int], object] = load_arial_font,
) -> TextLayout:
    from PIL import Image, ImageDraw

    image = Image.new("RGB", canvas_size, BACKGROUND_COLOR)
    draw = ImageDraw.Draw(image)
    max_width = int(canvas_size[0] * (1 - (2 * HORIZONTAL_MARGIN_RATIO)))
    max_height = int(canvas_size[1] * (1 - (2 * VERTICAL_MARGIN_RATIO)))
    max_font_size = min(canvas_size[0] // 3, canvas_size[1] // 4, 220)

    best_layout = None
    for size in range(max_font_size, MIN_FONT_SIZE - 1, -2):
        font = font_loader(size)
        lines = wrap_text_lines(text, max_width, draw, font)
        line_gap = max(2, int(size * LINE_SPACING_RATIO))
        measured = [_measure_text(draw, font, line) for line in lines]
        widest = max((width for width, _ in measured), default=0)
        tallest = max((height for _, height in measured), default=size)
        total_height = sum(height for _, height in measured)
        total_height += line_gap * max(0, len(lines) - 1)
        layout = TextLayout(
            lines=lines,
            font_size=size,
            line_height=max(tallest, size),
            total_height=total_height,
            max_width=widest,
        )
        best_layout = layout
        if widest <= max_width and total_height <= max_height:
            return layout

    return best_layout or TextLayout(lines=[""], font_size=MIN_FONT_SIZE, line_height=MIN_FONT_SIZE, total_height=MIN_FONT_SIZE, max_width=0)


def render_text_label(text: str, out_path: str) -> str:
    from PIL import Image, ImageDraw

    canvas_size = label_pixel_size()
    normalized = normalize_text(text)
    if not normalized:
        raise ValueError("Missing text")

    image = Image.new("RGB", canvas_size, BACKGROUND_COLOR)
    draw = ImageDraw.Draw(image)
    layout = plan_text_layout(normalized, canvas_size)
    font = load_arial_font(layout.font_size)
    line_gap = max(2, int(layout.font_size * LINE_SPACING_RATIO))
    current_y = (canvas_size[1] - layout.total_height) // 2

    for line in layout.lines:
        width, height = _measure_text(draw, font, line)
        x = (canvas_size[0] - width) // 2
        draw.text((x, current_y), line, font=font, fill=TEXT_COLOR)
        current_y += height + line_gap

    image.save(out_path, "PNG", dpi=(LABEL_DPI, LABEL_DPI))
    return out_path
