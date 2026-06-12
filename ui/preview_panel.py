import re
import tkinter as tk

import customtkinter as ctk


class PreviewPanel(ctk.CTkFrame):
    """Painel de visualização textual em formato de folha."""

    def __init__(self, master: ctk.CTkFrame, on_refresh=None) -> None:
        super().__init__(
            master,
            fg_color="#0B1F16",
            corner_radius=14,
            border_width=1,
            border_color="#244B36",
        )
        self.on_refresh = on_refresh
        self.zoom_value = ctk.StringVar(value="100%")
        self.marker_count = 0

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_header()
        self._build_toolbar()
        self._build_page()
        self._build_footer()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 10))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header,
            text="▣",
            font=("Segoe UI", 24, "bold"),
            text_color="#39FF7A",
        ).grid(row=0, column=0, rowspan=2, sticky="nw", padx=(0, 12))

        ctk.CTkLabel(
            header,
            text="Visualização do Documento",
            font=("Segoe UI", 18, "bold"),
            text_color="#39FF7A",
            anchor="w",
        ).grid(row=0, column=1, sticky="ew")

        ctk.CTkLabel(
            header,
            text="Preview atualizado automaticamente conforme você preenche os campos.",
            font=("Segoe UI", 12),
            text_color="#CBD5E1",
            anchor="w",
        ).grid(row=1, column=1, sticky="ew", pady=(3, 0))

    def _build_toolbar(self) -> None:
        toolbar = ctk.CTkFrame(self, fg_color="#10291D", corner_radius=10, border_width=1, border_color="#244B36")
        toolbar.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 12))
        toolbar.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            toolbar,
            text="▤",
            width=36,
            height=36,
            corner_radius=8,
            fg_color="#132F22",
            text_color="#39FF7A",
            font=("Segoe UI", 18, "bold"),
        ).grid(row=0, column=0, padx=(12, 10), pady=12)

        model_box = ctk.CTkFrame(toolbar, fg_color="transparent")
        model_box.grid(row=0, column=1, sticky="ew", pady=12)
        ctk.CTkLabel(
            model_box,
            text="Modelo carregado:",
            font=("Segoe UI", 11),
            text_color="#CBD5E1",
            anchor="w",
        ).pack(anchor="w")
        self.model_label = ctk.CTkLabel(
            model_box,
            text="Nenhum modelo",
            font=("Segoe UI", 12, "bold"),
            text_color="#F8FAFC",
            anchor="w",
        )
        self.model_label.pack(anchor="w", pady=(3, 0))

        ctk.CTkOptionMenu(
            toolbar,
            values=["75%", "90%", "100%", "110%", "125%"],
            variable=self.zoom_value,
            fg_color="#132F22",
            button_color="#132F22",
            button_hover_color="#16A34A",
            text_color="#F8FAFC",
            dropdown_fg_color="#10291D",
            dropdown_hover_color="#16A34A",
            width=120,
            command=self._apply_zoom,
        ).grid(row=0, column=2, padx=(10, 8), pady=12)

        for text, command in (("-", self._zoom_out), ("+", self._zoom_in)):
            ctk.CTkButton(
                toolbar,
                text=text,
                width=42,
                fg_color="#132F22",
                hover_color="#16A34A",
                text_color="#39FF7A",
                font=("Segoe UI", 16, "bold"),
                command=command,
            ).grid(row=0, column=3 if text == "-" else 4, padx=4, pady=12)

        ctk.CTkButton(
            toolbar,
            text="Atualizar",
            width=110,
            fg_color="#132F22",
            hover_color="#16A34A",
            text_color="#F8FAFC",
            command=self.on_refresh,
        ).grid(row=0, column=5, padx=(8, 12), pady=12)

    def _build_page(self) -> None:
        viewer = ctk.CTkFrame(self, fg_color="#07130D", corner_radius=10)
        viewer.grid(row=2, column=0, sticky="nsew", padx=18, pady=(0, 0))
        viewer.grid_columnconfigure(0, weight=1)
        viewer.grid_rowconfigure(0, weight=1)

        page_frame = tk.Frame(viewer, bg="#07130D", highlightthickness=0)
        page_frame.grid(row=0, column=0, sticky="nsew", padx=14, pady=14)
        page_frame.grid_columnconfigure(0, weight=1)
        page_frame.grid_rowconfigure(0, weight=1)

        self.page = tk.Text(
            page_frame,
            bg="#FFFFFF",
            fg="#020617",
            insertbackground="#020617",
            relief="flat",
            borderwidth=0,
            wrap="word",
            padx=70,
            pady=42,
            font=("Segoe UI", 12),
            spacing1=2,
            spacing3=8,
        )
        self.page.grid(row=0, column=0, sticky="nsew")

        scrollbar = tk.Scrollbar(page_frame, command=self.page.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.page.configure(yscrollcommand=scrollbar.set)
        self.page.tag_configure("marker", foreground="#008F45", font=("Segoe UI", 12, "bold"))
        self.page.configure(state="disabled")

    def _build_footer(self) -> None:
        footer = ctk.CTkFrame(self, fg_color="#10291D", corner_radius=8)
        footer.grid(row=3, column=0, sticky="ew", padx=18, pady=(8, 12))
        footer.grid_columnconfigure(3, weight=1)

        self.page_label = ctk.CTkLabel(footer, text="Página 1 de 2", text_color="#F8FAFC", font=("Segoe UI", 11))
        self.page_label.grid(row=0, column=0, padx=(12, 10), pady=7)

        self.words_label = ctk.CTkLabel(footer, text="0 palavras", text_color="#F8FAFC", font=("Segoe UI", 11))
        self.words_label.grid(row=0, column=1, padx=10, pady=7)

        self.chars_label = ctk.CTkLabel(footer, text="0 caracteres", text_color="#F8FAFC", font=("Segoe UI", 11))
        self.chars_label.grid(row=0, column=2, padx=10, pady=7)

        self.marker_badge = ctk.CTkLabel(
            footer,
            text="0 marcadores detectados",
            fg_color="#0E7A34",
            text_color="#39FF7A",
            corner_radius=6,
            font=("Segoe UI", 11),
        )
        self.marker_badge.grid(row=0, column=4, padx=12, pady=7)

    def set_text(self, text: str) -> None:
        content = text or "Selecione um template .docx para visualizar o documento."
        self.page.configure(state="normal")
        self.page.delete("1.0", "end")
        self.page.insert("1.0", content)
        self._highlight_markers(content)
        self.page.configure(state="disabled")
        self._update_counts(content)

    def set_meta(self, text: str) -> None:
        if text and " | " in text:
            file_name = text.split(" | ", 1)[0]
            self.set_model_name(file_name)

    def set_model_name(self, name: str) -> None:
        self.model_label.configure(text=name or "Nenhum modelo")

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
        values = ["75%", "90%", "100%", "110%", "125%"]
        index = max(0, values.index(self.zoom_value.get()) - 1)
        self.zoom_value.set(values[index])
        self._apply_zoom(values[index])

    def _zoom_in(self) -> None:
        values = ["75%", "90%", "100%", "110%", "125%"]
        index = min(len(values) - 1, values.index(self.zoom_value.get()) + 1)
        self.zoom_value.set(values[index])
        self._apply_zoom(values[index])

    def _apply_zoom(self, value: str) -> None:
        size = {
            "75%": 9,
            "90%": 11,
            "100%": 12,
            "110%": 13,
            "125%": 15,
        }.get(value, 12)
        self.page.configure(font=("Segoe UI", size))
        self.page.tag_configure("marker", font=("Segoe UI", size, "bold"))
