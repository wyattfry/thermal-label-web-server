import subprocess
from typing import List, Optional

from .settings import APP_DIR, PRINTER, PRINT_SETTINGS
from .sumatra_manager import ensure_sumatra_available


def send_to_printer(paths: List[str]) -> Optional[str]:
    try:
        sumatra_exe = ensure_sumatra_available(APP_DIR)
        for print_path in paths:
            subprocess.run(
                [
                    sumatra_exe,
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
    except (OSError, RuntimeError) as exc:
        return f"Printer setup failed: {exc}"
    return None
