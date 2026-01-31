import logging
import os
import sys
import threading

import win32event
import win32service
import win32serviceutil
import servicemanager

SERVICE_PORT = 8088
SERVICE_APP_PATH = ""


def _parse_args(argv):
    port = None
    app_path = None
    for idx, arg in enumerate(argv):
        if arg == "--port" and idx + 1 < len(argv):
            port = argv[idx + 1]
        if arg == "--app-path" and idx + 1 < len(argv):
            app_path = argv[idx + 1]
    return port, app_path


def _configure_paths(app_path):
    if not app_path:
        return
    if os.path.isfile(app_path):
        base = os.path.dirname(app_path)
    else:
        base = app_path
    if base:
        os.chdir(base)
        if base not in sys.path:
            sys.path.insert(0, base)


def _configure_logging():
    try:
        from server.settings import LOG_DIR
        os.makedirs(LOG_DIR, exist_ok=True)
        log_path = os.path.join(LOG_DIR, "service.log")
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(message)s",
            handlers=[logging.FileHandler(log_path, encoding="ascii", errors="replace")],
        )
    except Exception:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


port_arg, app_path_arg = _parse_args(sys.argv)
if port_arg:
    try:
        SERVICE_PORT = int(port_arg)
    except ValueError:
        pass
if app_path_arg:
    SERVICE_APP_PATH = app_path_arg
_configure_paths(SERVICE_APP_PATH)

from server import create_app


class LabelUploadService(win32serviceutil.ServiceFramework):
    _svc_name_ = "LabelUpload"
    _svc_display_name_ = "Thermal Label Printer"
    _svc_description_ = "Thermal label upload web server"

    def __init__(self, args):
        super().__init__(args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)

    def SvcDoRun(self):
        _configure_logging()
        logging.info("Starting Thermal Label Printer service on port %s", SERVICE_PORT)
        servicemanager.LogInfoMsg("Starting Thermal Label Printer service")
        app = create_app()

        def run_app():
            app.run(host="0.0.0.0", port=SERVICE_PORT, use_reloader=False)

        thread = threading.Thread(target=run_app, daemon=True)
        thread.start()

        win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)
        logging.info("Stopping Thermal Label Printer service")
        servicemanager.LogInfoMsg("Stopping Thermal Label Printer service")
        os._exit(0)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(LabelUploadService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(LabelUploadService)
