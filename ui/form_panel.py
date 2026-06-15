from datetime import date

import customtkinter as ctk


class FormPanel(ctk.CTkFrame):
    """Painel lateral com os campos de preenchimento e acoes."""

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
    PLACEHOLDER = "#94A3B8"
    ENTRY_BORDER = "#315A43"
    ENTRY_BORDER_REQUIRED = "#315A43"
    ENTRY_BORDER_ERROR = "#EF4444"

    REQUIRED_MARKERS = {"{{COMPRADOR}}", "{{CPF_CNPJ}}", "{{VENDEDOR}}"}

    FIELD_GROUPS = [
        {
            "title": "Dados do Comprador",
            "icon": "▣",
            "rows": [
                [
                    ("Nome Completo", "{{COMPRADOR}}", "Digite o nome completo"),
                    ("Nacionalidade", "{{NACIONALIDADE}}", "Digite a nacionalidade"),
                    ("Profissão", "{{PROFISSAO}}", "Digite a profissão"),
                ],
                [
                    ("Estado Civil", "{{ESTADO_CIVIL}}", "Digite o estado civil"),
                    ("CPF / CNPJ", "{{CPF_CNPJ}}", "Digite o CPF ou CNPJ"),
                ],
            ],
        },
        {
            "title": "Dados do Imóvel",
            "icon": "▦",
            "rows": [
                [
                    ("Lote / Unidade", "{{LOTE}}", "Ex.: 04 ou 1203"),
                    ("Quadra", "{{QUADRA}}", "Ex.: 08B"),
                    ("Empreendimento", "{{EMPREENDIMENTO}}", "Ex.: Alphaville Ribeirão Preto"),
                ],
            ],
        },
        {
            "title": "Dados do Vendedor",
            "icon": "▣",
            "rows": [[("Nome do Vendedor", "{{VENDEDOR}}", "Digite o nome do vendedor")]],
        },
        {
            "title": "Dados do Documento",
            "icon": "▤",
            "rows": [
                [
                    ("Cidade", "{{CIDADE}}", "Ex.: Ribeirão Preto"),
                    ("Data", "{{DATA}}", "Ex.: 01 de Junho de 2026"),
                ],
            ],
        },
    ]

    def __init__(self, master: ctk.CTkFrame, on_update, callbacks: dict) -> None:
        super().__init__(
            master,
            fg_color=self.SURFACE,
            corner_radius=10,
            border_width=1,
            border_color=self.BORDER,
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
            text="Preencha os Dados",
            font=("Segoe UI", 18, "bold"),
            text_color=self.GREEN_NEON,
            anchor="w",
        ).grid(row=0, column=1, sticky="ew")

        ctk.CTkLabel(
            header,
            text="Insira as informações para preencher o documento.",
            font=("Segoe UI", 12),
            text_color=self.MUTED,
            anchor="w",
        ).grid(row=1, column=1, sticky="ew", pady=(2, 0))

    def _build_content(self) -> None:
        self.content = ctk.CTkScrollableFrame(
            self,
            fg_color=self.SURFACE,
            corner_radius=9,
            scrollbar_fg_color=self.SURFACE,
            scrollbar_button_color="#64748B",
            scrollbar_button_hover_color="#94A3B8",
        )
        self.content.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self.content.grid_columnconfigure(0, weight=1)

        for row, group in enumerate(self.FIELD_GROUPS):
            self._build_field_card(row, group)

        self._build_actions_card(len(self.FIELD_GROUPS))

    def _build_field_card(self, row: int, group: dict) -> None:
        card = ctk.CTkFrame(
            self.content,
            fg_color=self.PANEL,
            corner_radius=9,
            border_width=1,
            border_color=self.BORDER,
        )
        card.grid(row=row, column=0, sticky="ew", padx=0, pady=(0, 12))
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card,
            text=f"{group['icon']}  {group['title']}",
            font=("Segoe UI", 13, "bold"),
            text_color=self.GREEN_NEON,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 11))

        for index, fields in enumerate(group["rows"], start=1):
            self._build_field_row(card, index, fields)

    def _build_field_row(self, card: ctk.CTkFrame, row: int, fields: list[tuple[str, str, str]]) -> None:
        row_frame = ctk.CTkFrame(card, fg_color="transparent")
        row_frame.grid(row=row, column=0, sticky="ew", padx=14, pady=(0, 14 if row == 1 else 12))
        for column in range(len(fields)):
            row_frame.grid_columnconfigure(column, weight=1, uniform=f"row-{row}")

        for column, (label, marker, placeholder) in enumerate(fields):
            field = ctk.CTkFrame(row_frame, fg_color="transparent")
            field.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 10, 0))
            field.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                field,
                text=label,
                font=("Segoe UI", 11, "bold"),
                text_color=self.TEXT,
                anchor="w",
            ).grid(row=0, column=0, sticky="ew", pady=(0, 6))

            entry_frame = ctk.CTkFrame(field, fg_color="transparent")
            entry_frame.grid(row=1, column=0, sticky="ew")
            entry_frame.grid_columnconfigure(0, weight=1)

            entry = ctk.CTkEntry(
                entry_frame,
                placeholder_text=placeholder,
                fg_color=self.BG,
                border_color=self.ENTRY_BORDER,
                border_width=1,
                text_color=self.TEXT,
                placeholder_text_color=self.PLACEHOLDER,
                height=34,
                corner_radius=6,
                font=("Segoe UI", 12),
            )
            entry.grid(row=0, column=0, sticky="ew")
            entry.bind("<KeyRelease>", lambda event=None, _marker=marker: self._handle_key_update(_marker))
            self.entries[marker] = entry

            if marker == "{{DATA}}":
                ctk.CTkButton(
                    entry_frame,
                    text="▣",
                    width=36,
                    height=34,
                    fg_color=self.CARD,
                    hover_color=self.GREEN_HOVER,
                    text_color=self.GREEN_NEON,
                    border_width=1,
                    border_color=self.BORDER,
                    corner_radius=6,
                    font=("Segoe UI Symbol", 13, "bold"),
                    command=self._fill_today,
                ).grid(row=0, column=1, padx=(6, 0))

    def _build_actions_card(self, row: int) -> None:
        card = ctk.CTkFrame(
            self.content,
            fg_color=self.PANEL,
            corner_radius=9,
            border_width=1,
            border_color=self.BORDER,
        )
        card.grid(row=row, column=0, sticky="ew", padx=0, pady=(0, 2))
        for column in range(4):
            card.grid_columnconfigure(column, weight=1, uniform="action-buttons")

        ctk.CTkLabel(
            card,
            text="✦  Ações",
            font=("Segoe UI", 13, "bold"),
            text_color=self.GREEN_NEON,
            anchor="w",
        ).grid(row=0, column=0, columnspan=4, sticky="ew", padx=14, pady=(14, 10))

        actions = [
            ("▣", "Selecionar\nTemplate", self.callbacks.get("select_template"), self.CARD, self.GREEN_HOVER),
            ("▰", "Pasta de\nSaída", self.callbacks.get("select_output"), self.CARD, self.GREEN_HOVER),
            ("✓", "Gerar\nDocumento", self.callbacks.get("generate"), self.GREEN_HOVER, self.GREEN),
            ("⌧", "Limpar\nCampos", self.callbacks.get("clear"), self.CARD, self.GREEN_HOVER),
        ]

        for column, (icon, text, command, color, hover) in enumerate(actions):
            button = ctk.CTkButton(
                card,
                text=f"{icon}\n{text}",
                height=76,
                fg_color=color,
                hover_color=hover,
                text_color=self.TEXT,
                border_width=1,
                border_color=self.BORDER,
                corner_radius=8,
                font=("Segoe UI", 12, "bold"),
                command=command,
            )
            button.grid(
                row=1,
                column=column,
                sticky="ew",
                padx=(12 if column == 0 else 5, 12 if column == 3 else 5),
                pady=(0, 14),
            )

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
        return None

    def set_output_info(self, text: str) -> None:
        return None

    def clear(self) -> None:
        for entry in self.entries.values():
            entry.delete(0, "end")
        self.clear_validation()
        self._notify_update()
