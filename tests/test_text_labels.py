from pathlib import Path

from PIL import Image
from PIL import ImageDraw

from server.text_labels import (
    label_pixel_size,
    load_arial_font,
    plan_text_layout,
    render_text_label,
    wrap_text_lines,
)


def non_white_bbox(image: Image.Image):
    mask = image.convert("L").point(lambda value: 0 if value > 250 else 255)
    return mask.getbbox()


def test_wrap_text_lines_splits_long_single_word():
    image = Image.new("RGB", (600, 600), "white")
    draw = ImageDraw.Draw(image)
    font = load_arial_font(48)

    lines = wrap_text_lines("SUPERLONGSTORAGECONTAINERIDENTIFIER", 220, draw, font)

    assert len(lines) > 1


def test_plan_text_layout_shrinks_for_longer_text():
    size = label_pixel_size()

    short_layout = plan_text_layout("Bin A1", size)
    long_layout = plan_text_layout(
        "Seasonal winter decorations for upper shelving section seven",
        size,
    )

    assert long_layout.font_size < short_layout.font_size


def test_render_text_label_creates_centered_label_image(tmp_path: Path):
    out_path = tmp_path / "label.png"

    render_text_label("Back Stock", str(out_path))

    assert out_path.exists()
    with Image.open(out_path) as image:
        assert image.size == label_pixel_size()
        bbox = non_white_bbox(image)
        assert bbox is not None
        text_center_x = (bbox[0] + bbox[2]) / 2
        text_center_y = (bbox[1] + bbox[3]) / 2
        image_center_x = image.width / 2
        image_center_y = image.height / 2
        assert abs(text_center_x - image_center_x) < image.width * 0.08
        assert abs(text_center_y - image_center_y) < image.height * 0.08
