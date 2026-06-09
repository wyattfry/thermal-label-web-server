import io
from pathlib import Path

import server
import server.routes as routes
import server.utils as utils


def create_test_app(tmp_path: Path, monkeypatch):
    upload_dir = tmp_path / "uploads"
    log_dir = tmp_path / "logs"

    monkeypatch.setattr(server, "UPLOAD_DIR", str(upload_dir))
    monkeypatch.setattr(server, "LOG_DIR", str(log_dir))
    monkeypatch.setattr(routes, "UPLOAD_DIR", str(upload_dir))
    monkeypatch.setattr(utils, "UPLOAD_DIR", str(upload_dir))
    monkeypatch.setattr(utils, "LOG_DIR", str(log_dir))

    return server.create_app(), upload_dir


def test_preview_text_generates_preview_file(tmp_path, monkeypatch):
    app, upload_dir = create_test_app(tmp_path, monkeypatch)
    client = app.test_client()

    response = client.post("/preview-text", data={"text": "Storage A\nShelf 4"})

    assert response.status_code == 200
    assert b"Print" in response.data
    generated = list(upload_dir.glob("*-text-label.png"))
    assert len(generated) == 1
    assert generated[0].name.encode() in response.data


def test_print_processed_cleans_up_generated_preview(tmp_path, monkeypatch):
    app, upload_dir = create_test_app(tmp_path, monkeypatch)
    client = app.test_client()
    preview_path = upload_dir / "preview-text-label.png"
    preview_path.parent.mkdir(parents=True, exist_ok=True)
    preview_path.write_bytes(b"preview")

    monkeypatch.setattr(routes, "send_to_printer", lambda paths: None)

    response = client.post("/print-processed", data={"files": [preview_path.name]})

    assert response.status_code == 302
    assert not preview_path.exists()


def test_index_shows_enter_text_action(tmp_path, monkeypatch):
    app, _ = create_test_app(tmp_path, monkeypatch)
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b"Enter Text" in response.data


def test_image_preview_does_not_require_sumatra(tmp_path, monkeypatch):
    app, upload_dir = create_test_app(tmp_path, monkeypatch)
    client = app.test_client()

    response = client.post(
        "/print",
        data={
            "action": "preview",
            "mode": "fit",
            "file": (io.BytesIO(png_bytes()), "label.png"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert b"Print Preview" in response.data
    assert list(upload_dir.glob("*_processed.png"))


def test_print_setup_failure_is_shown_to_user(tmp_path, monkeypatch):
    app, upload_dir = create_test_app(tmp_path, monkeypatch)
    client = app.test_client()
    preview_path = upload_dir / "preview.png"
    preview_path.parent.mkdir(parents=True, exist_ok=True)
    preview_path.write_bytes(b"preview")
    monkeypatch.setattr(
        routes,
        "send_to_printer",
        lambda paths: "Printer setup failed: unavailable",
    )

    response = client.post("/print-processed", data={"files": [preview_path.name]})

    assert response.status_code == 200
    assert b"Printer setup failed: unavailable" in response.data
    assert preview_path.exists()


def test_missing_route_remains_404(tmp_path, monkeypatch):
    app, _ = create_test_app(tmp_path, monkeypatch)

    response = app.test_client().get("/favicon.ico")

    assert response.status_code == 404


def png_bytes():
    from PIL import Image

    output = io.BytesIO()
    Image.new("RGB", (40, 60), "white").save(output, "PNG")
    return output.getvalue()
