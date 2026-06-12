import sys

import customtkinter as ctk

from ui.main_window import DocFillProApp


def main() -> None:
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("green")

    initial_template = sys.argv[1] if len(sys.argv) > 1 else None
    app = DocFillProApp(initial_template=initial_template)
    app.mainloop()


if __name__ == "__main__":
    main()
