import subprocess
from typing import List, Optional

from .settings import APP_DIR, PRINTER, PRINT_SETTINGS, SUMATRA
from .sumatra_manager import ensure_sumatra_available


def send_to_printer(paths: List[str]) -> Optional[str]:
    # Ensure SumatraPDF is available (download if necessary)
    sumatra_exe = ensure_sumatra_available(APP_DIR)
    
    try:
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
    return None
