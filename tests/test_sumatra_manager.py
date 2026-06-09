import io
import zipfile

from server import sumatra_manager


class DownloadResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


def test_download_sumatra_sends_user_agent_and_extracts(tmp_path, monkeypatch):
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as zip_file:
        zip_file.writestr("SumatraPDF-3.5.2-64.exe", b"sumatra")

    captured = {}

    def fake_urlopen(request, timeout):
        captured["user_agent"] = request.get_header("User-agent")
        captured["timeout"] = timeout
        return DownloadResponse(archive.getvalue())

    monkeypatch.setattr(sumatra_manager.urllib.request, "urlopen", fake_urlopen)

    result = sumatra_manager.download_sumatra(str(tmp_path))

    assert captured["user_agent"] == sumatra_manager.DOWNLOAD_USER_AGENT
    assert captured["timeout"] == 60
    assert result == str(tmp_path / ".sumatrapdf" / "SumatraPDF.exe")
    assert (tmp_path / ".sumatrapdf" / "SumatraPDF.exe").read_bytes() == b"sumatra"
