import math
import re
import tkinter as tk

import customtkinter as ctk

from ui.i18n import t
from ui.symbol_manager import SymbolManager
from ui.theme import COLORS, font, symbol_font


class PreviewPanel(ctk.CTkFrame):
    """Painel de preview com folha A4 centralizada."""

    ZOOM_STEPS = [60, 75, 90, 100, 110, 125, 150]

    def __init__(self, master: ctk.CTkFrame, on_refresh=None) -> None:
        super().__init__(
            master,
            fg_color=COLORS["bg2"],
            corner_radius=0,
            border_width=0,
        )
        self.on_refresh = on_refresh
        self.zoom_percent = 100
        self.marker_count = 0
        self._content = ""
        self._empty_state = True
        self._empty_symbol_image = SymbolManager.get_symbol_with_opacity("empty", opacity=0.18, size=72)
        self._empty_symbol_widget = None
        self._loading_symbol_images = [
            SymbolManager.get_symbol_with_opacity("loading", opacity=0.36, size=48),
            SymbolManager.get_symbol_with_opacity("loading", opacity=0.62, size=48),
        ]
        self._loading_symbol_widget = None
        self._loading_job = None
        self._loading_symbol_index = 0

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_header()
        self._build_toolbar()
        self._build_preview()
        self._build_footer()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color=COLORS["bg2"], corner_radius=0)
        header.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 8))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header,
            text="▤",
            width=22,
            text_color=COLORS["green3"],
            font=symbol_font(18, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=(0, 8))

        ctk.CTkLabel(
            header,
            text=t("preview_title"),
            text_color=COLORS["text"],
            font=font(13, "bold"),
            anchor="w",
        ).grid(row=0, column=1, sticky="ew")

        ctk.CTkLabel(
            header,
            text=t("preview_hint"),
            text_color=COLORS["text3"],
            font=font(10),
            anchor="e",
        ).grid(row=0, column=2, sticky="e", padx=(10, 0))

    def _build_toolbar(self) -> None:
        toolbar = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg3"],
            corner_radius=8,
            border_width=1,
            border_color=COLORS["border"],
        )
        toolbar.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 10))
        toolbar.grid_columnconfigure(1, weight=1)

        file_badge = ctk.CTkFrame(toolbar, fg_color=COLORS["bg4"], corner_radius=6)
        file_badge.grid(row=0, column=0, sticky="w", padx=(10, 8), pady=9)
        file_badge.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            file_badge,
            text="▣",
            width=28,
            text_color=COLORS["green3"],
            font=symbol_font(15, "bold"),
        ).grid(row=0, column=0, rowspan=2, sticky="nsw", padx=(8, 7), pady=6)

        ctk.CTkLabel(
            file_badge,
            text=t("preview_model"),
            text_color=COLORS["text3"],
            font=font(9, "bold"),
            anchor="w",
        ).grid(row=0, column=1, sticky="ew", padx=(0, 12), pady=(6, 0))

        self.model_label = ctk.CTkLabel(
            file_badge,
            text=t("preview_none"),
            text_color=COLORS["text2"],
            font=font(11),
            anchor="w",
        )
        self.model_label.grid(row=1, column=1, sticky="ew", padx=(0, 12), pady=(0, 6))

        zoom_group = ctk.CTkFrame(toolbar, fg_color=COLORS["bg2"], corner_radius=6, border_width=1, border_color=COLORS["border2"])
        zoom_group.grid(row=0, column=2, sticky="e", padx=(8, 8), pady=9)
        for col in range(3):
            zoom_group.grid_columnconfigure(col, weight=0)

        ctk.CTkButton(
            zoom_group,
            text="−",
            width=30,
            height=28,
            fg_color="transparent",
            hover_color=COLORS["bg4"],
            text_color=COLORS["green3"],
            font=font(14, "bold"),
            command=self._zoom_out,
        ).grid(row=0, column=0, padx=(2, 0), pady=2)

        self.zoom_label = ctk.CTkLabel(
            zoom_group,
            text="100%",
            width=48,
            text_color=COLORS["text"],
            font=font(11, "bold"),
        )
        self.zoom_label.grid(row=0, column=1, padx=2, pady=2)

        ctk.CTkButton(
            zoom_group,
            text="+",
            width=30,
            height=28,
            fg_color="transparent",
            hover_color=COLORS["bg4"],
            text_color=COLORS["green3"],
            font=font(14, "bold"),
            command=self._zoom_in,
        ).grid(row=0, column=2, padx=(0, 2), pady=2)

        ctk.CTkButton(
            toolbar,
            text=t("preview_refresh"),
            width=104,
            height=32,
            fg_color="transparent",
            hover_color=COLORS["bg4"],
            text_color=COLORS["green4"],
            border_width=1,
            border_color=COLORS["border2"],
            corner_radius=6,
            font=font(11, "bold"),
            command=self.on_refresh,
        ).grid(row=0, column=3, sticky="e", padx=(0, 10), pady=9)

    def _build_preview(self) -> None:
        viewer = ctk.CTkFrame(self, fg_color=COLORS["bg"], corner_radius=0)
        viewer.grid(row=2, column=0, sticky="nsew", padx=14, pady=(0, 0))
        viewer.grid_columnconfigure(0, weight=1)
        viewer.grid_rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(viewer, bg=COLORS["bg"], highlightthickness=0, bd=0)
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=(10, 2), pady=10)

        self.scrollbar = ctk.CTkScrollbar(
            viewer,
            orientation="vertical",
            command=self.canvas.yview,
            width=12,
            fg_color=COLORS["bg"],
            button_color="#64748B",
            button_hover_color=COLORS["text3"],
            corner_radius=8,
        )
        self.scrollbar.grid(row=0, column=1, sticky="ns", padx=(0, 8), pady=10)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.shadow = ctk.CTkFrame(self.canvas, fg_color="#D9E2E8", corner_radius=3)
        self.page = ctk.CTkFrame(
            self.shadow,
            fg_color="#FFFFFF",
            corner_radius=2,
            border_width=1,
            border_color="#E2E8F0",
        )
        self.page.grid(row=0, column=0, sticky="nsew", padx=(0, 3), pady=(0, 3))
        self.page.grid_columnconfigure(0, weight=1)
        self.page.grid_rowconfigure(0, weight=1)

        self.text = tk.Text(
            self.page,
            bg="#FFFFFF",
            fg="#020617",
            insertbackground="#020617",
            relief="flat",
            borderwidth=0,
            wrap="word",
            padx=32,
            pady=36,
            font=("Segoe UI", 11),
            spacing1=1,
            spacing2=1,
            spacing3=6,
            cursor="arrow",
            takefocus=False,
        )
        self.text.grid(row=0, column=0, sticky="nsew")
        self.text.tag_configure("marker", foreground="#16A34A", background="#F0FDF4", font=("Segoe UI", 11, "bold"))
        self.text.tag_configure("empty", foreground=COLORS["text3"], justify="center", font=("Segoe UI", 12))
        self.text.configure(state="disabled")

        self.page_window = self.canvas.create_window(0, 18, window=self.shadow, anchor="n")
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.text.bind("<MouseWheel>", self._on_mousewheel)
        self.page.bind("<MouseWheel>", self._on_mousewheel)
        self.shadow.bind("<MouseWheel>", self._on_mousewheel)

    def _build_footer(self) -> None:
        footer = ctk.CTkFrame(self, fg_color=COLORS["bg3"], corner_radius=8)
        footer.grid(row=3, column=0, sticky="ew", padx=14, pady=(8, 10))
        footer.grid_columnconfigure(5, weight=1)

        self.page_label = ctk.CTkLabel(footer, text="Página 1 de 1", text_color=COLORS["text2"], font=font(10))
        self.page_label.grid(row=0, column=0, padx=(10, 7), pady=6)

        ctk.CTkLabel(footer, text="•", text_color=COLORS["text3"], font=font(10, "bold")).grid(row=0, column=1, padx=2, pady=6)

        self.words_label = ctk.CTkLabel(footer, text="0 palavras", text_color=COLORS["text2"], font=font(10))
        self.words_label.grid(row=0, column=2, padx=7, pady=6)

        ctk.CTkLabel(footer, text="•", text_color=COLORS["text3"], font=font(10, "bold")).grid(row=0, column=3, padx=2, pady=6)

        self.chars_label = ctk.CTkLabel(footer, text="0 caracteres", text_color=COLORS["text2"], font=font(10))
        self.chars_label.grid(row=0, column=4, padx=7, pady=6)

        self.marker_badge = ctk.CTkLabel(
            footer,
            text="0 " + t("preview_marker_badge"),
            fg_color="#0E7A34",
            text_color=COLORS["green4"],
            corner_radius=5,
            font=font(10, "bold"),
        )
        self.marker_badge.grid(row=0, column=6, padx=10, pady=6)

    def set_text(self, text: str) -> None:
        self._stop_loading()
        content = text or t("preview_empty")
        self._empty_state = not bool(text) or content.rstrip(".") == t("preview_empty")
        self._content = content

        self.text.configure(state="normal")
        if self._empty_symbol_widget is not None:
            self._empty_symbol_widget.destroy()
            self._empty_symbol_widget = None
        self.text.delete("1.0", "end")

        if self._empty_state:
            self.text.insert("1.0", "\n\n\n")
            if self._empty_symbol_image is not None:
                self._empty_symbol_widget = ctk.CTkLabel(
                    self.text,
                    image=self._empty_symbol_image,
                    text="",
                    fg_color="#FFFFFF",
                )
                self.text.window_create("end", window=self._empty_symbol_widget)
                self.text.insert("end", "\n\n" + t("preview_empty") + "\n" + t("preview_empty_hint"))
            else:
                self.text.insert("end", "▤\n\n" + t("preview_empty") + "\n" + t("preview_empty_hint"))
            self.text.tag_add("empty", "1.0", "end")
        else:
            self.text.insert("1.0", content)
            self._highlight_markers(content)

        self.text.configure(state="disabled")
        self._update_counts(content)
        self.after_idle(self._update_page_geometry)

    def set_loading(self, message: str) -> None:
        self._empty_state = True
        self._content = message
        self.text.configure(state="normal")
        if self._empty_symbol_widget is not None:
            self._empty_symbol_widget.destroy()
            self._empty_symbol_widget = None
        if self._loading_symbol_widget is not None:
            self._loading_symbol_widget.destroy()
            self._loading_symbol_widget = None
        self.text.delete("1.0", "end")
        self.text.insert("1.0", "\n\n\n")

        loading_image = self._current_loading_symbol()
        if loading_image is not None:
            self._loading_symbol_widget = ctk.CTkLabel(
                self.text,
                image=loading_image,
                text="",
                fg_color="#FFFFFF",
            )
            self.text.window_create("end", window=self._loading_symbol_widget)
            self.text.insert("end", "\n\n" + message)
            self._pulse_loading_symbol()
        else:
            self.text.insert("end", "▤\n\n" + message)

        self.text.tag_add("empty", "1.0", "end")
        self.text.configure(state="disabled")
        self._update_counts(message)
        self.after_idle(self._update_page_geometry)

    def set_meta(self, text: str) -> None:
        if text and " | " in text:
            self.set_model_name(text.split(" | ", 1)[0])

    def set_model_name(self, name: str) -> None:
        label = name or t("preview_none")
        if len(label) > 54:
            label = f"...{label[-51:]}"
        self.model_label.configure(text=label)

    def set_marker_count(self, count: int) -> None:
        self.marker_count = max(0, count)
        self.marker_badge.configure(text=f"{self.marker_count} " + t("preview_marker_badge"))

    def _highlight_markers(self, content: str) -> None:
        self.text.tag_remove("marker", "1.0", "end")
        for match in re.finditer(r"\{\{[^{}]+\}\}", content):
            self.text.tag_add("marker", f"1.0+{match.start()}c", f"1.0+{match.end()}c")

    def _current_loading_symbol(self):
        available = [image for image in self._loading_symbol_images if image is not None]
        if not available:
            return None
        return available[self._loading_symbol_index % len(available)]

    def _pulse_loading_symbol(self) -> None:
        if self._loading_symbol_widget is None:
            return
        self._loading_symbol_index += 1
        image = self._current_loading_symbol()
        if image is not None:
            self._loading_symbol_widget.configure(image=image)
        self._loading_job = self.after(1000, self._pulse_loading_symbol)

    def _stop_loading(self) -> None:
        if self._loading_job is not None:
            try:
                self.after_cancel(self._loading_job)
            except Exception:
                pass
            self._loading_job = None
        if self._loading_symbol_widget is not None:
            self._loading_symbol_widget.destroy()
            self._loading_symbol_widget = None

    def _update_counts(self, content: str) -> None:
        words = len(re.findall(r"\S+", content))
        chars = len(content)
        pages = max(1, math.ceil(chars / 2600))
        self.page_label.configure(text=f"Página 1 de {pages}")
        self.words_label.configure(text=f"{words:,} palavras".replace(",", "."))
        self.chars_label.configure(text=f"{chars:,} caracteres".replace(",", "."))

    def _zoom_out(self) -> None:
        index = max(0, self.ZOOM_STEPS.index(self.zoom_percent) - 1)
        self.zoom_percent = self.ZOOM_STEPS[index]
        self._apply_zoom()

    def _zoom_in(self) -> None:
        index = min(len(self.ZOOM_STEPS) - 1, self.ZOOM_STEPS.index(self.zoom_percent) + 1)
        self.zoom_percent = self.ZOOM_STEPS[index]
        self._apply_zoom()

    def _apply_zoom(self) -> None:
        self.zoom_label.configure(text=f"{self.zoom_percent}%")
        font_size = max(8, int(11 * self.zoom_percent / 100))
        self.text.configure(font=("Segoe UI", font_size))
        self.text.tag_configure("marker", foreground="#16A34A", background="#F0FDF4", font=("Segoe UI", font_size, "bold"))
        self.text.tag_configure("empty", foreground=COLORS["text3"], justify="center", font=("Segoe UI", max(10, font_size)))
        self._update_page_geometry()

    def _on_canvas_resize(self, _event=None) -> None:
        self._update_page_geometry()

    def _on_mousewheel(self, event) -> str:
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"

    def _update_page_geometry(self) -> None:
        canvas_width = max(self.canvas.winfo_width(), 500)
        scale = self.zoom_percent / 100
        page_width = int(620 * scale)
        page_height = max(int(page_width * 1.414), self._estimate_content_height(page_width))
        self.shadow.configure(width=page_width + 3, height=page_height + 3)
        self.shadow.grid_propagate(False)
        self.page.configure(width=page_width, height=page_height)
        self.page.grid_propagate(False)
        pad_x = max(24, int(32 * scale))
        pad_y = max(28, int(36 * scale))
        self.text.configure(padx=pad_x, pady=pad_y)
        self.canvas.coords(self.page_window, max(canvas_width // 2, page_width // 2 + 24), 18)
        self.canvas.configure(scrollregion=(0, 0, max(canvas_width, page_width + 80), page_height + 42))

    def _estimate_content_height(self, page_width: int) -> int:
        font_size = max(8, int(11 * self.zoom_percent / 100))
        chars_per_line = max(36, int((page_width - 72) / max(5.6, font_size * 0.54)))
        lines = self._content.splitlines() or [""]
        visual_lines = sum(max(1, math.ceil(len(line) / chars_per_line)) for line in lines)
        return 96 + visual_lines * max(14, int(font_size * 1.8))
