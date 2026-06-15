import sys

import customtkinter as ctk

from ui.i18n import detect_language, set_language
from ui.main_window import DocFillProApp


def _parse_args(argv: list[str]) -> tuple[str, str | None]:
    lang = detect_language("pt")
    template_path: str | None = None

    index = 1
    while index < len(argv):
        item = argv[index]
        if item.startswith("--lang="):
            lang = item.split("=", 1)[1].strip().lower() or lang
            index += 1
            continue
        if item in ("--lang", "-lang") and index + 1 < len(argv):
            lang = argv[index + 1].strip().lower()
            index += 2
            continue
        if item.startswith("--"):
            index += 1
            continue
        if template_path is None:
            template_path = item
        index += 1

    return lang, template_path


def main() -> None:
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("green")

    lang, initial_template = _parse_args(sys.argv)
    set_language(lang)

    app = DocFillProApp(initial_template=initial_template, language=lang)
    app.mainloop()


if __name__ == "__main__":
    main()
