import subprocess
from typing import List, Optional

from .settings import PRINTER, PRINT_SETTINGS, SUMATRA


def send_to_printer(paths: List[str]) -> Optional[str]:
    try:
        for print_path in paths:
            subprocess.run(
                [
                    SUMATRA,
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
