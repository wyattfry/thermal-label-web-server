# AGENTS.md

## Project Overview
- Name: label-upload
- Purpose: Windows Flask app that uploads files and prints 4x6 labels on a USB thermal printer (SumatraPDF backend).
- Current entrypoint: app.py
- Runtime: Windows, Flask, SumatraPDF, optional PyMuPDF + Pillow.

## Environment
- Working dir: C:\label-upload
- Printer: configured in app.py (PRINTER)
- PDF viewer/print tool: SumatraPDF (SUMATRA path in app.py)
- Uploads/logs: C:\label-upload\uploads, C:\label-upload\logs

## How Agents Should Work
- Prefer small, incremental changes with clear acceptance criteria.
- Keep changes ASCII-only unless file already uses Unicode.
- Do not remove user changes or revert unrelated changes.
- If a change is large (structure or config), propose a plan before editing.

## Current Priorities (in order)
1) Convert hard-coded config into a proper config file.
2) Split the single Python file into a conventional project layout.
3) Update README.md with prerequisites + install/run steps.
4) UI redesign to a simpler upload/preview/print flow.
5) Add PowerShell installer to install/enable/disable/uninstall as a Windows service.
6) Delete uploaded files after printing (including processed/debug artifacts).

## Task Notes and Acceptance Criteria
### 1) Config file
- Add a config file (e.g., config.json or .env).
- Move APP_DIR, SUMATRA, PRINTER, PRINT_SETTINGS, LABEL_DPI, etc.
- App should boot with defaults if config is missing.

### 2) Project structure
- Break app.py into a package (app/, templates/, static/, etc.).
- Keep behavior unchanged unless explicitly requested.

### 3) README
- Document prerequisites: Python, SumatraPDF, optional PyMuPDF/Pillow.
- Include install/run steps and how to configure printer/path.

### 4) UI redesign
- Prefer a minimal UI with Upload + Print, hidden advanced options.
- After upload, show preview; on mobile, scale to viewport.
- Print button should show progress and outcome message overlay.
- If simpler: keep current design but hide advanced controls behind "Advanced".

### 5) Windows service helper
- Provide a single PS1 script: install/enable/disable/uninstall.
- Should be idempotent and safe to re-run.

### 6) Cleanup after printing
- Delete uploaded and derived files after successful print.
- Ensure multi-page PDFs are handled safely.

## Files of Interest
- app.py
- uploads/
- logs/
- README.md (to be updated)

## Testing Guidance
- There are no automated tests yet.
- Validate by uploading a PDF/image and verifying preview + print behavior.
