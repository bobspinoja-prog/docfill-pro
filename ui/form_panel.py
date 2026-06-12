from datetime import date

import customtkinter as ctk


class FormPanel(ctk.CTkFrame):
    """Painel lateral com os campos de preenchimento e ações."""

    REQUIRED_MARKERS = {"{{COMPRADOR}}", "{{CPF_CNPJ}}", "{{VENDEDOR}}"}
    ENTRY_BORDER = "#315A43"
    ENTRY_BORDER_REQUIRED = "#315A43"
    ENTRY_BORDER_ERROR = "#EF4444"

    FIELD_DEFINITIONS = [
        ("Dados do Comprador", [
            ("Nome Completo", "{{COMPRADOR}}", "Digite o nome completo"),
            ("Nacionalidade", "{{NACIONALIDADE}}", "Digite a nacionalidade"),
            ("Profissão", "{{PROFISSAO}}", "Digite a profissão"),
            ("Estado Civil", "{{ESTADO_CIVIL}}", "Digite o estado civil"),
            ("CPF / CNPJ", "{{CPF_CNPJ}}", "Digite o CPF ou CNPJ"),
        ]),
        ("Dados do Imóvel", [
            ("Lote / Unidade", "{{LOTE}}", "Ex.: 04 ou 1203"),
            ("Quadra", "{{QUADRA}}", "Ex.: 08B"),
            ("Empreendimento", "{{EMPREENDIMENTO}}", "Ex.: Alphaville Ribeirão Preto"),
        ]),
        ("Dados do Vendedor", [
            ("Nome do Vendedor", "{{VENDEDOR}}", "Digite o nome do vendedor"),
        ]),
        ("Dados do Documento", [
            ("Cidade", "{{CIDADE}}", "Ex.: Ribeirão Preto"),
            ("Data", "{{DATA}}", "Ex.: 01 de Junho de 2026"),
        ]),
    ]

    def __init__(self, master: ctk.CTkFrame, on_update, callbacks: dict) -> None:
        super().__init__(
            master,
            fg_color="#0B1F16",
            corner_radius=14,
            border_width=1,
            border_color="#244B36",
        )
        self.on_update = on_update
        self.callbacks = callbacks
        self.entries = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_content()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 12))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header,
            text="▤",
            font=("Segoe UI", 24, "bold"),
            text_color="#39FF7A",
        ).grid(row=0, column=0, rowspan=2, sticky="nw", padx=(0, 12))

        ctk.CTkLabel(
            header,
            text="Preencha os Dados",
            font=("Segoe UI", 18, "bold"),
            text_color="#39FF7A",
            anchor="w",
        ).grid(row=0, column=1, sticky="ew")

        ctk.CTkLabel(
            header,
            text="Insira as informações para preencher o documento.",
            font=("Segoe UI", 12),
            text_color="#CBD5E1",
            anchor="w",
        ).grid(row=1, column=1, sticky="ew", pady=(3, 0))

    def _build_content(self) -> None:
        self.content = ctk.CTkScrollableFrame(self, fg_color="#0B1F16", corner_radius=10)
        self.content.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self.content.grid_columnconfigure(0, weight=1)

        for row, (title, fields) in enumerate(self.FIELD_DEFINITIONS):
            self._build_field_card(row, title, fields)

        self._build_actions_card(len(self.FIELD_DEFINITIONS))

    def _build_field_card(self, row: int, title: str, fields: list[tuple[str, str, str]]) -> None:
        card = ctk.CTkFrame(
            self.content,
            fg_color="#10291D",
            corner_radius=12,
            border_width=1,
            border_color="#244B36",
        )
        card.grid(row=row, column=0, sticky="ew", padx=0, pady=(0, 12))
        columns = 3 if len(fields) >= 3 else 2
        for column in range(columns):
            card.grid_columnconfigure(column, weight=1, uniform=f"{title}-columns")

        ctk.CTkLabel(
            card,
            text=title,
            font=("Segoe UI", 13, "bold"),
            text_color="#39FF7A",
            anchor="w",
        ).grid(row=0, column=0, columnspan=columns, sticky="ew", padx=14, pady=(14, 10))

        for index, (label, marker, placeholder) in enumerate(fields):
            field_row = 1 + (index // columns) * 2
            field_col = index % columns
            span = columns if len(fields) == 1 else 1
            if title == "Dados do Documento":
                span = 1

            ctk.CTkLabel(
                card,
                text=label,
                font=("Segoe UI", 11, "bold"),
                text_color="#F8FAFC",
                anchor="w",
            ).grid(row=field_row, column=field_col, columnspan=span, sticky="ew", padx=14, pady=(0, 5))

            entry_frame = ctk.CTkFrame(card, fg_color="transparent")
            entry_frame.grid(row=field_row + 1, column=field_col, columnspan=span, sticky="ew", padx=14, pady=(0, 14))
            entry_frame.grid_columnconfigure(0, weight=1)

            entry = ctk.CTkEntry(
                entry_frame,
                placeholder_text=placeholder,
                fg_color="#07130D",
                border_color=self.ENTRY_BORDER,
                text_color="#F8FAFC",
                placeholder_text_color="#94A3B8",
                height=34,
            )
            entry.grid(row=0, column=0, sticky="ew")
            entry.bind("<KeyRelease>", lambda event=None, _marker=marker: self._handle_key_update(_marker))
            self.entries[marker] = entry

            if marker == "{{DATA}}":
                ctk.CTkButton(
                    entry_frame,
                    text="Hoje",
                    width=52,
                    height=34,
                    fg_color="#132F22",
                    hover_color="#16A34A",
                    text_color="#39FF7A",
                    command=self._fill_today,
                ).grid(row=0, column=1, padx=(6, 0))

    def _build_actions_card(self, row: int) -> None:
        card = ctk.CTkFrame(
            self.content,
            fg_color="#10291D",
            corner_radius=12,
            border_width=1,
            border_color="#244B36",
        )
        card.grid(row=row, column=0, sticky="ew", padx=0, pady=(0, 4))
        for column in range(4):
            card.grid_columnconfigure(column, weight=1, uniform="action-buttons")

        ctk.CTkLabel(
            card,
            text="Ações",
            font=("Segoe UI", 13, "bold"),
            text_color="#39FF7A",
            anchor="w",
        ).grid(row=0, column=0, columnspan=4, sticky="ew", padx=14, pady=(14, 10))

        actions = [
            ("Selecionar\nTemplate", self.callbacks.get("select_template"), "#132F22"),
            ("Pasta de\nSaída", self.callbacks.get("select_output"), "#132F22"),
            ("Gerar\nDocumento", self.callbacks.get("generate"), "#16A34A"),
            ("Limpar\nCampos", self.callbacks.get("clear"), "#132F22"),
        ]

        for column, (text, command, color) in enumerate(actions):
            button = ctk.CTkButton(
                card,
                text=text,
                height=74,
                fg_color=color,
                hover_color="#22C55E",
                text_color="#F8FAFC",
                font=("Segoe UI", 12, "bold"),
                command=command,
            )
            button.grid(row=1, column=column, sticky="ew", padx=(14 if column == 0 else 5, 14 if column == 3 else 5), pady=(0, 14))

    def _notify_update(self) -> None:
        if self.on_update:
            self.on_update()

    def _handle_key_update(self, marker: str) -> None:
        if marker in self.REQUIRED_MARKERS:
            self.entries[marker].configure(border_color=self.ENTRY_BORDER_REQUIRED)
        self._notify_update()

    def _fill_today(self) -> None:
        months = [
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
        ]
        today = date.today()
        entry = self.entries.get("{{DATA}}")
        if entry is None:
            return
        entry.delete(0, "end")
        entry.insert(0, f"{today.day:02d} de {months[today.month - 1]} de {today.year}")
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
        for entry in self.entries.values():
            entry.configure(border_color=self.ENTRY_BORDER)

    def set_template_info(self, text: str) -> None:
        # Mantido para compatibilidade com a janela principal.
        return None

    def set_output_info(self, text: str) -> None:
        # Mantido para compatibilidade com a janela principal.
        return None

    def clear(self) -> None:
        for entry in self.entries.values():
            entry.delete(0, "end")
        self.clear_validation()
        self._notify_update()
