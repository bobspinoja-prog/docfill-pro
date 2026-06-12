import customtkinter as ctk


class FormPanel(ctk.CTkFrame):
    """Painel lateral com os campos de preenchimento e ações."""

    REQUIRED_MARKERS = {"{{COMPRADOR}}", "{{CPF_CNPJ}}", "{{VENDEDOR}}"}
    ENTRY_BORDER = "#22543D"
    ENTRY_BORDER_REQUIRED = "#D97706"
    ENTRY_BORDER_ERROR = "#EF4444"

    FIELD_DEFINITIONS = [
        ("DADOS DO COMPRADOR", [
            ("Nome Completo", "{{COMPRADOR}}"),
            ("Nacionalidade", "{{NACIONALIDADE}}"),
            ("Profissão", "{{PROFISSAO}}"),
            ("Estado Civil", "{{ESTADO_CIVIL}}"),
            ("CPF/CNPJ", "{{CPF_CNPJ}}"),
        ]),
        ("DADOS DO IMÓVEL", [
            ("Lote / Unidade", "{{LOTE}}"),
            ("Quadra", "{{QUADRA}}"),
            ("Empreendimento", "{{EMPREENDIMENTO}}"),
        ]),
        ("DADOS DO VENDEDOR", [
            ("Nome do Vendedor", "{{VENDEDOR}}"),
        ]),
        ("DADOS DO DOCUMENTO", [
            ("Cidade", "{{CIDADE}}"),
            ("Data", "{{DATA}}"),
        ]),
    ]

    def __init__(self, master: ctk.CTkFrame, on_update, callbacks: dict) -> None:
        super().__init__(
            master,
            fg_color="#0B2418",
            corner_radius=8,
            border_width=1,
            border_color="#22543D",
        )
        self.on_update = on_update
        self.callbacks = callbacks
        self.entries = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.configure(width=460)

        self._build_header()
        self._build_actions()
        self._build_scrollable_fields()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="Campos de Troca",
            font=("Segoe UI", 20, "bold"),
            text_color="#F2FBF5",
            anchor="w",
        ).grid(row=0, column=0, sticky="ew")

        ctk.CTkLabel(
            header,
            text="Preencha os dados que substituirão o conteúdo do Word.",
            font=("Segoe UI", 12),
            text_color="#B7C9BC",
            anchor="w",
            wraplength=390,
        ).grid(row=1, column=0, sticky="ew", pady=(4, 0))

    def _build_actions(self) -> None:
        action_card = ctk.CTkFrame(self, fg_color="#103522", corner_radius=8)
        action_card.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 10))
        action_card.grid_columnconfigure(0, weight=1)
        action_card.grid_columnconfigure(1, weight=1)

        self.template_info = ctk.CTkLabel(
            action_card,
            text="Word: nenhum arquivo carregado",
            text_color="#B7C9BC",
            font=("Segoe UI", 11),
            anchor="w",
            justify="left",
            wraplength=390,
        )
        self.template_info.grid(row=0, column=0, columnspan=2, sticky="ew", padx=12, pady=(12, 4))

        self.output_info = ctk.CTkLabel(
            action_card,
            text="Saída: escolher ao gerar",
            text_color="#B7C9BC",
            font=("Segoe UI", 11),
            anchor="w",
            justify="left",
            wraplength=390,
        )
        self.output_info.grid(row=1, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 10))

        buttons = [
            ("Adicionar Word (.docx)", self.callbacks.get("select_template"), 2, 0, 2),
            ("Escolher Pasta", self.callbacks.get("select_output"), 3, 0, 1),
            ("Gerar Documento", self.callbacks.get("generate"), 3, 1, 1),
            ("Limpar Campos", self.callbacks.get("clear"), 4, 0, 2),
        ]

        for text, command, row, col, span in buttons:
            button = ctk.CTkButton(
                action_card,
                text=text,
                fg_color="#22C55E" if text != "Limpar Campos" else "#15803D",
                hover_color="#16A34A",
                text_color="#F2FBF5",
                command=command,
            )
            button.grid(
                row=row,
                column=col,
                columnspan=span,
                sticky="ew",
                padx=12 if span == 2 else (12, 6) if col == 0 else (6, 12),
                pady=(0, 8),
            )

    def _build_scrollable_fields(self) -> None:
        self.field_area = ctk.CTkScrollableFrame(self, fg_color="#0B2418", corner_radius=8)
        self.field_area.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 12))
        self.field_area.grid_columnconfigure(0, weight=1)

        for index, (title, fields) in enumerate(self.FIELD_DEFINITIONS):
            self._build_field_card(index, title, fields)

    def _build_field_card(self, row: int, title: str, fields: list[tuple[str, str]]) -> None:
        card = ctk.CTkFrame(self.field_area, fg_color="#06140D", corner_radius=8)
        card.grid(row=row, column=0, sticky="ew", padx=6, pady=7)
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card,
            text=title,
            font=("Segoe UI", 14, "bold"),
            text_color="#F2FBF5",
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 4))

        field_row = 1
        for label, marker in fields:
            label_text = f"{label} *" if marker in self.REQUIRED_MARKERS else label
            ctk.CTkLabel(
                card,
                text=label_text,
                text_color="#B7C9BC",
                anchor="w",
            ).grid(row=field_row, column=0, sticky="ew", padx=12, pady=(7, 0))

            entry = ctk.CTkEntry(
                card,
                placeholder_text=marker,
                fg_color="#071A12",
                border_color=self.ENTRY_BORDER_REQUIRED if marker in self.REQUIRED_MARKERS else self.ENTRY_BORDER,
                text_color="#F2FBF5",
            )
            entry.grid(row=field_row + 1, column=0, sticky="ew", padx=12, pady=(3, 8))
            entry.bind("<KeyRelease>", lambda event=None, _marker=marker: self._handle_key_update(_marker))
            self.entries[marker] = entry
            field_row += 2

    def _notify_update(self) -> None:
        if self.on_update:
            self.on_update()

    def _handle_key_update(self, marker: str) -> None:
        if marker in self.REQUIRED_MARKERS:
            self.entries[marker].configure(border_color=self.ENTRY_BORDER_REQUIRED)
        self._notify_update()

    def get_values(self) -> dict:
        return {marker: entry.get().strip() for marker, entry in self.entries.items()}

    def set_values(self, values: dict, only_empty: bool = True) -> int:
        updated = 0
        for marker, value in values.items():
            entry = self.entries.get(marker)
            if entry is None:
                continue
            if only_empty and entry.get().strip():
                continue
            entry.delete(0, "end")
            entry.insert(0, str(value))
            updated += 1
        if updated:
            self.clear_validation()
            self._notify_update()
        return updated

    def get_missing_required(self) -> list[str]:
        return [
            marker
            for marker in self.REQUIRED_MARKERS
            if not self.entries[marker].get().strip()
        ]

    def mark_missing_required(self, missing_markers: list[str]) -> None:
        missing = set(missing_markers)
        for marker in self.REQUIRED_MARKERS:
            border = self.ENTRY_BORDER_ERROR if marker in missing else self.ENTRY_BORDER_REQUIRED
            self.entries[marker].configure(border_color=border)

    def clear_validation(self) -> None:
        for marker, entry in self.entries.items():
            border = self.ENTRY_BORDER_REQUIRED if marker in self.REQUIRED_MARKERS else self.ENTRY_BORDER
            entry.configure(border_color=border)

    def set_template_info(self, text: str) -> None:
        self.template_info.configure(text=f"Word: {text}")

    def set_output_info(self, text: str) -> None:
        self.output_info.configure(text=f"Saída: {text}")

    def clear(self) -> None:
        for entry in self.entries.values():
            entry.delete(0, "end")
        self.clear_validation()
        self._notify_update()
