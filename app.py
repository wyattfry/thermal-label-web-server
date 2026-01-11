import os
import socket

from label_upload import create_app


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
    app = create_app()
    app.run(host=host, port=port, use_reloader=False)
