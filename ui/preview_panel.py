import math
import re
import tkinter as tk

import customtkinter as ctk


class PreviewPanel(ctk.CTkFrame):
    """Painel de visualizacao textual com folha centralizada."""

    BG = "#07130D"
    SURFACE = "#0B1F16"
    PANEL = "#10291D"
    CARD = "#132F22"
    BORDER = "#244B36"
    GREEN = "#22C55E"
    GREEN_HOVER = "#16A34A"
    GREEN_NEON = "#39FF7A"
    TEXT = "#F8FAFC"
    MUTED = "#CBD5E1"
    PAPER_TEXT = "#020617"

    ZOOM_VALUES = ["75%", "90%", "100%", "110%", "125%"]

    def __init__(self, master: ctk.CTkFrame, on_refresh=None) -> None:
        super().__init__(
            master,
            fg_color=self.SURFACE,
            corner_radius=10,
            border_width=1,
            border_color=self.BORDER,
        )
        self.on_refresh = on_refresh
        self.zoom_value = ctk.StringVar(value="100%")
        self.marker_count = 0
        self._content = ""
        self._page_width = 720

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_header()
        self._build_toolbar()
        self._build_page()
        self._build_footer()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(18, 12))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header,
            text="▤",
            width=30,
            font=("Segoe UI Symbol", 26, "bold"),
            text_color=self.GREEN_NEON,
        ).grid(row=0, column=0, rowspan=2, sticky="nw", padx=(0, 12), pady=(1, 0))

        ctk.CTkLabel(
            header,
            text="Visualização do Documento",
            font=("Segoe UI", 18, "bold"),
            text_color=self.GREEN_NEON,
            anchor="w",
        ).grid(row=0, column=1, sticky="ew")

        ctk.CTkLabel(
            header,
            text="Preview atualizado automaticamente conforme você preenche os campos.",
            font=("Segoe UI", 12),
            text_color=self.MUTED,
            anchor="w",
        ).grid(row=1, column=1, sticky="ew", pady=(2, 0))

    def _build_toolbar(self) -> None:
        toolbar = ctk.CTkFrame(
            self,
            fg_color=self.PANEL,
            corner_radius=9,
            border_width=1,
            border_color=self.BORDER,
        )
        toolbar.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 12))
        toolbar.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            toolbar,
            text="▣",
            width=38,
            height=38,
            corner_radius=8,
            fg_color=self.CARD,
            text_color=self.GREEN_NEON,
            font=("Segoe UI Symbol", 19, "bold"),
        ).grid(row=0, column=0, padx=(12, 10), pady=12)

        model_box = ctk.CTkFrame(toolbar, fg_color="transparent")
        model_box.grid(row=0, column=1, sticky="ew", pady=12)
        ctk.CTkLabel(
            model_box,
            text="Modelo carregado:",
            font=("Segoe UI", 11),
            text_color=self.MUTED,
            anchor="w",
        ).pack(anchor="w")
        self.model_label = ctk.CTkLabel(
            model_box,
            text="Nenhum modelo",
            font=("Segoe UI", 12, "bold"),
            text_color=self.TEXT,
            anchor="w",
        )
        self.model_label.pack(anchor="w", pady=(3, 0))

        ctk.CTkOptionMenu(
            toolbar,
            values=self.ZOOM_VALUES,
            variable=self.zoom_value,
            fg_color=self.CARD,
            button_color=self.CARD,
            button_hover_color=self.GREEN_HOVER,
            text_color=self.TEXT,
            dropdown_fg_color=self.PANEL,
            dropdown_hover_color=self.GREEN_HOVER,
            dropdown_text_color=self.TEXT,
            width=120,
            height=40,
            corner_radius=8,
            font=("Segoe UI", 12, "bold"),
            command=self._apply_zoom,
        ).grid(row=0, column=2, padx=(10, 8), pady=12)

        for column, (text, command) in enumerate((("−", self._zoom_out), ("+", self._zoom_in)), start=3):
            ctk.CTkButton(
                toolbar,
                text=text,
                width=42,
                height=40,
                fg_color=self.CARD,
                hover_color=self.GREEN_HOVER,
                text_color=self.GREEN_NEON,
                border_width=1,
                border_color=self.BORDER,
                corner_radius=8,
                font=("Segoe UI", 17, "bold"),
                command=command,
            ).grid(row=0, column=column, padx=4, pady=12)

        ctk.CTkButton(
            toolbar,
            text="↻  Atualizar",
            width=112,
            height=40,
            fg_color=self.CARD,
            hover_color=self.GREEN_HOVER,
            text_color=self.TEXT,
            border_width=1,
            border_color=self.BORDER,
            corner_radius=8,
            font=("Segoe UI", 12, "bold"),
            command=self.on_refresh,
        ).grid(row=0, column=5, padx=(8, 12), pady=12)

    def _build_page(self) -> None:
        viewer = ctk.CTkFrame(self, fg_color=self.BG, corner_radius=9)
        viewer.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 0))
        viewer.grid_columnconfigure(0, weight=1)
        viewer.grid_rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(viewer, bg=self.BG, highlightthickness=0, bd=0)
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=(12, 4), pady=12)

        self.scrollbar = ctk.CTkScrollbar(
            viewer,
            orientation="vertical",
            command=self.canvas.yview,
            width=12,
            fg_color=self.PANEL,
            button_color="#64748B",
            button_hover_color="#94A3B8",
            corner_radius=8,
        )
        self.scrollbar.grid(row=0, column=1, sticky="ns", padx=(0, 6), pady=12)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.page_shell = tk.Frame(
            self.canvas,
            bg="#FFFFFF",
            width=720,
            height=1018,
            highlightbackground="#E2E8F0",
            highlightthickness=1,
        )
        self.page_shell.pack_propagate(False)
        self.page_window = self.canvas.create_window(0, 18, window=self.page_shell, anchor="n")

        self.page = tk.Text(
            self.page_shell,
            bg="#FFFFFF",
            fg=self.PAPER_TEXT,
            insertbackground=self.PAPER_TEXT,
            relief="flat",
            borderwidth=0,
            wrap="word",
            padx=70,
            pady=42,
            font=("Segoe UI", 12),
            spacing1=2,
            spacing2=1,
            spacing3=8,
            takefocus=False,
            cursor="arrow",
        )
        self.page.pack(fill="both", expand=True)
        self.page.tag_configure("marker", foreground="#008F45", font=("Segoe UI", 12, "bold"))
        self.page.configure(state="disabled")

        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.page.bind("<MouseWheel>", self._on_mousewheel)
        self.page_shell.bind("<MouseWheel>", self._on_mousewheel)

    def _build_footer(self) -> None:
        footer = ctk.CTkFrame(self, fg_color=self.PANEL, corner_radius=8)
        footer.grid(row=3, column=0, sticky="ew", padx=20, pady=(8, 12))
        footer.grid_columnconfigure(3, weight=1)

        self.page_label = ctk.CTkLabel(footer, text="Página 1 de 2", text_color=self.TEXT, font=("Segoe UI", 11))
        self.page_label.grid(row=0, column=0, padx=(12, 10), pady=7)

        ctk.CTkLabel(footer, text="•", text_color=self.MUTED, font=("Segoe UI", 12, "bold")).grid(row=0, column=1, padx=(0, 0), pady=7)

        self.words_label = ctk.CTkLabel(footer, text="0 palavras", text_color=self.TEXT, font=("Segoe UI", 11))
        self.words_label.grid(row=0, column=2, padx=10, pady=7)

        self.chars_label = ctk.CTkLabel(footer, text="0 caracteres", text_color=self.TEXT, font=("Segoe UI", 11))
        self.chars_label.grid(row=0, column=3, sticky="w", padx=(8, 10), pady=7)

        self.marker_badge = ctk.CTkLabel(
            footer,
            text="0 marcadores detectados",
            fg_color="#0E7A34",
            text_color=self.GREEN_NEON,
            corner_radius=6,
            font=("Segoe UI", 11),
        )
        self.marker_badge.grid(row=0, column=4, padx=12, pady=7)

    def set_text(self, text: str) -> None:
        content = text or "Selecione um template .docx para visualizar o documento."
        self._content = content
        self.page.configure(state="normal")
        self.page.delete("1.0", "end")
        self.page.insert("1.0", content)
        self._highlight_markers(content)
        self.page.configure(state="disabled")
        self._update_counts(content)
        self.after_idle(self._update_page_geometry)

    def set_meta(self, text: str) -> None:
        if text and " | " in text:
            file_name = text.split(" | ", 1)[0]
            self.set_model_name(file_name)

    def set_model_name(self, name: str) -> None:
        label = name or "Nenhum modelo"
        if len(label) > 46:
            label = f"...{label[-43:]}"
        self.model_label.configure(text=label)

    def set_marker_count(self, count: int) -> None:
        self.marker_count = max(0, count)
        self.marker_badge.configure(text=f"{self.marker_count} marcadores detectados")

    def _highlight_markers(self, content: str) -> None:
        self.page.tag_remove("marker", "1.0", "end")
        for match in re.finditer(r"\{\{[^{}]+\}\}", content):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.page.tag_add("marker", start, end)

    def _update_counts(self, content: str) -> None:
        words = len(re.findall(r"\S+", content))
        chars = len(content)
        self.words_label.configure(text=f"{words:,} palavras".replace(",", "."))
        self.chars_label.configure(text=f"{chars:,} caracteres".replace(",", "."))

    def _zoom_out(self) -> None:
        index = max(0, self.ZOOM_VALUES.index(self.zoom_value.get()) - 1)
        self.zoom_value.set(self.ZOOM_VALUES[index])
        self._apply_zoom(self.ZOOM_VALUES[index])

    def _zoom_in(self) -> None:
        index = min(len(self.ZOOM_VALUES) - 1, self.ZOOM_VALUES.index(self.zoom_value.get()) + 1)
        self.zoom_value.set(self.ZOOM_VALUES[index])
        self._apply_zoom(self.ZOOM_VALUES[index])

    def _apply_zoom(self, value: str) -> None:
        size = {
            "75%": 9,
            "90%": 11,
            "100%": 12,
            "110%": 13,
            "125%": 15,
        }.get(value, 12)
        self.page.configure(font=("Segoe UI", size))
        self.page.tag_configure("marker", foreground="#008F45", font=("Segoe UI", size, "bold"))
        self.after_idle(self._update_page_geometry)

    def _on_canvas_resize(self, event=None) -> None:
        self._update_page_geometry()

    def _on_mousewheel(self, event) -> str:
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"

    def _update_page_geometry(self) -> None:
        canvas_width = max(self.canvas.winfo_width(), 600)
        page_width = min(max(canvas_width - 64, 540), 760)
        self._page_width = page_width
        page_height = max(int(page_width * 1.414), self._estimate_content_height(page_width))

        self.page_shell.configure(width=page_width, height=page_height)
        self.page.configure(padx=max(48, int(page_width * 0.10)), pady=max(38, int(page_width * 0.055)))
        self.canvas.coords(self.page_window, canvas_width // 2, 18)
        self.canvas.configure(scrollregion=(0, 0, max(canvas_width, page_width + 80), page_height + 36))

    def _estimate_content_height(self, page_width: int) -> int:
        font_size = {
            "75%": 9,
            "90%": 11,
            "100%": 12,
            "110%": 13,
            "125%": 15,
        }.get(self.zoom_value.get(), 12)
        chars_per_line = max(48, int((page_width - 150) / max(6.3, font_size * 0.56)))
        lines = self._content.splitlines() or [""]
        visual_lines = sum(max(1, math.ceil(len(line) / chars_per_line)) for line in lines)
        return 124 + (visual_lines * int(font_size * 1.75)) + (self._content.count("\n\n") * 8)
