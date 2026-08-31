from __future__ import annotations

import customtkinter as ctk

from ui.i18n import t
from ui.symbol_manager import SymbolManager
from ui.theme import COLORS, font


class AboutWindow(ctk.CTkToplevel):
    """Small 'About DocFill Pro' dialog."""

    def __init__(self, master) -> None:
        super().__init__(master)
        self.title(t("about_title"))
        self.geometry("420x280")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["bg"])
        self.grid_columnconfigure(0, weight=1)

        content = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        content.grid(row=0, column=0, sticky="nsew", padx=24, pady=24)
        content.grid_columnconfigure(0, weight=1)

        self._symbol_image = SymbolManager.get_symbol("empty", size=72)
        if self._symbol_image is not None:
            ctk.CTkLabel(content, image=self._symbol_image, text="", fg_color="transparent").grid(row=0, column=0, pady=(0, 14))

        ctk.CTkLabel(
            content,
            text=t("app_name"),
            text_color=COLORS["text"],
            font=font(18, "bold"),
        ).grid(row=1, column=0, pady=(0, 6))

        ctk.CTkLabel(
            content,
            text=t("about_text"),
            text_color=COLORS["text2"],
            font=font(11),
            justify="center",
            wraplength=340,
        ).grid(row=2, column=0, pady=(0, 18))

        ctk.CTkButton(
            content,
            text=t("close"),
            width=120,
            height=32,
            fg_color=COLORS["green2"],
            hover_color=COLORS["green"],
            text_color=COLORS["text"],
            corner_radius=6,
            command=self.withdraw,
        ).grid(row=3, column=0)
