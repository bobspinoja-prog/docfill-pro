#!/usr/bin/env python3
"""Generate a JSON report for DocFill Pro visual asset integration."""

from datetime import datetime
import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
ICONS_DIR = ASSETS_DIR / "icons"
REPORT_PATH = PROJECT_ROOT / "docs" / "dev-notes" / "ASSETS_INTEGRATION_REPORT.json"


def _status(value: bool) -> str:
    return "ok" if value else "missing"


def _print_check(label: str, value: bool) -> None:
    marker = "[OK]" if value else "[MISSING]"
    print(f"  {marker} {label}")


def _list_pngs(prefix: str) -> list[str]:
    if not ICONS_DIR.exists():
        return []
    return sorted(path.name for path in ICONS_DIR.glob(f"{prefix}*.png"))


def generate_integration_report() -> int:
    external_source = ASSETS_DIR / "ICON_EXTERNAL.png"
    internal_source = ASSETS_DIR / "SYMBOL_INTERNAL.png"
    generated_ico = ICONS_DIR / "docfill.ico"
    app_icon = ASSETS_DIR / "app_icon.ico"
    symbol_manager = PROJECT_ROOT / "ui" / "symbol_manager.py"
    spec_file = PROJECT_ROOT / "DOCFILL PRO.spec"
    inno_file = PROJECT_ROOT / "installer" / "DOCFILL_PRO_Inno.iss"

    external_versions = _list_pngs("docfill_")
    internal_versions = _list_pngs("symbol_")

    external_ready = external_source.exists() and generated_ico.exists() and app_icon.exists() and bool(external_versions)
    internal_ready = internal_source.exists() and bool(internal_versions) and symbol_manager.exists()
    packaging_ready = spec_file.exists() and inno_file.exists() and app_icon.exists()
    all_ready = external_ready and internal_ready and packaging_ready

    report = {
        "data": datetime.now().isoformat(),
        "projeto": "DocFill Pro",
        "versao": "1.1.0",
        "paths": {
            "project_root": str(PROJECT_ROOT),
            "assets": str(ASSETS_DIR),
            "icons": str(ICONS_DIR),
        },
        "assets": {
            "external": {
                "source": str(external_source),
                "source_status": _status(external_source.exists()),
                "ico": str(generated_ico),
                "ico_status": _status(generated_ico.exists()),
                "app_icon": str(app_icon),
                "app_icon_status": _status(app_icon.exists()),
                "generated_pngs": external_versions,
                "ready": external_ready,
            },
            "internal": {
                "source": str(internal_source),
                "source_status": _status(internal_source.exists()),
                "generated_pngs": internal_versions,
                "symbol_manager_status": _status(symbol_manager.exists()),
                "ready": internal_ready,
            },
        },
        "packaging": {
            "spec_status": _status(spec_file.exists()),
            "inno_status": _status(inno_file.exists()),
            "ready": packaging_ready,
        },
        "usage": {
            "external_icon": [
                "Window icon: ui/main_window.py DocFillProApp._set_app_icon()",
                "Window/taskbar icon fallback: ui/main_window.py DocFillProApp._apply_window_icon()",
                "Executable icon: DOCFILL PRO.spec icon_path",
                "Installer wizard icon: installer/DOCFILL_PRO_Inno.iss SetupIconFile",
                "Installed app icon file: installer/DOCFILL_PRO_Inno.iss [Files] app_icon.ico",
                "Start menu shortcut icon: installer/DOCFILL_PRO_Inno.iss [Icons]",
                "Desktop shortcut icon: installer/DOCFILL_PRO_Inno.iss [Icons]",
            ],
            "internal_symbol": [
                "Header brand mark: ui/main_window.py DocFillProApp._build_header()",
                "Internal startup splash overlay: ui/main_window.py DocFillProApp._show_startup_splash()",
                "Right sidebar/form header: ui/form_panel.py FormPanel._build_header()",
                "Preview empty state: ui/preview_panel.py PreviewPanel.set_text()",
                "Preview placeholder/no document state: ui/preview_panel.py PreviewPanel.set_text()",
                "Preview loading state with pulse: ui/preview_panel.py PreviewPanel.set_loading()",
                "About dialog: ui/main_window.py DocFillProApp.show_about()",
            ],
        },
        "next_steps": [],
    }

    if not external_source.exists():
        report["next_steps"].append("Save ICON_EXTERNAL.png in assets/.")
    if not internal_source.exists():
        report["next_steps"].append("Save SYMBOL_INTERNAL.png in assets/.")
    if external_source.exists() and internal_source.exists() and not (generated_ico.exists() and internal_versions):
        report["next_steps"].append("Run: python scripts/process_assets.py")
    if not all_ready:
        report["next_steps"].append("Run this report again after processing assets.")

    print("=" * 70)
    print("DOCFILL PRO - ASSET INTEGRATION REPORT")
    print("=" * 70)
    print("\nFile structure")
    _print_check("assets/ICON_EXTERNAL.png", external_source.exists())
    _print_check("assets/SYMBOL_INTERNAL.png", internal_source.exists())
    _print_check("assets/icons/", ICONS_DIR.exists())
    _print_check("assets/icons/docfill.ico", generated_ico.exists())
    _print_check("assets/app_icon.ico", app_icon.exists())

    print("\nGenerated PNGs")
    if external_versions or internal_versions:
        for name in external_versions + internal_versions:
            print(f"  - {name}")
    else:
        print("  - none")

    print("\nConfiguration")
    _print_check("DOCFILL PRO.spec", spec_file.exists())
    _print_check("installer/DOCFILL_PRO_Inno.iss", inno_file.exists())
    _print_check("ui/symbol_manager.py", symbol_manager.exists())

    print("\nUsage map")
    print("  External icon:")
    for item in report["usage"]["external_icon"]:
        print(f"    - {item}")
    print("  Internal symbol:")
    for item in report["usage"]["internal_symbol"]:
        print(f"    - {item}")

    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nReport saved to: {REPORT_PATH}")

    if all_ready:
        print("[OK] Asset integration is complete.")
        return 0

    print("[PENDING] Asset integration is not complete yet.")
    for step in report["next_steps"]:
        print(f"  - {step}")
    return 1


if __name__ == "__main__":
    sys.exit(generate_integration_report())
