import os
import socket
import platform
import sys

from server import create_app


if __name__ == "__main__":
    if platform.system() != "Windows":
        raise SystemExit("This application can only run on Windows.")
    if sys.version_info < (3, 9, 0):
        raise SystemExit("Python version 3.9 or higher is required.")
    try:
        import flask  # noqa: F401
        import PIL  # noqa: F401
        import fitz  # noqa: F401
    except ImportError as exc:
        raise SystemExit(f"Missing required package: {exc.name}. Please install all dependencies.") from exc
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
    app = create_app()
    app.run(host=host, port=port, use_reloader=False)
