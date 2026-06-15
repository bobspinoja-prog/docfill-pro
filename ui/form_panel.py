from datetime import date

import customtkinter as ctk

from ui.theme import CARD_STYLE, COLORS, FIELD_STYLE, font, symbol_font


class CollapsibleCard(ctk.CTkFrame):
    """Card simples com header clicavel e corpo recolhivel."""

    def __init__(self, master, title: str, icon_char: str) -> None:
        super().__init__(master, **CARD_STYLE)
        self.expanded = True

        self.grid_columnconfigure(0, weight=1)

        self.header = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0, cursor="hand2")
        self.header.grid(row=0, column=0, sticky="ew", padx=10, pady=(9, 7))
        self.header.grid_columnconfigure(1, weight=1)

        self.icon_label = ctk.CTkLabel(
            self.header,
            text=icon_char,
            width=18,
            text_color=COLORS["green3"],
            font=symbol_font(13, "bold"),
        )
        self.icon_label.grid(row=0, column=0, sticky="w", padx=(0, 7))

        self.title_label = ctk.CTkLabel(
            self.header,
            text=title.upper(),
            text_color=COLORS["green3"],
            font=font(11, "bold"),
            anchor="w",
        )
        self.title_label.grid(row=0, column=1, sticky="ew")

        self.chevron = ctk.CTkLabel(
            self.header,
            text="⌄",
            width=18,
            text_color=COLORS["text3"],
            font=symbol_font(14, "bold"),
        )
        self.chevron.grid(row=0, column=2, sticky="e")

        self.body = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.body.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.body.grid_columnconfigure(0, weight=1)

        for widget in (self.header, self.icon_label, self.title_label, self.chevron):
            widget.bind("<Button-1>", self.toggle)

    def toggle(self, _event=None) -> None:
        if self.expanded:
            self.chevron.configure(text="›")
            self.expanded = False
            self.after(150, self.body.grid_remove)
            return

        self.body.grid()
        self.chevron.configure(text="⌄")
        self.expanded = True


class FormPanel(ctk.CTkFrame):
    """Painel lateral com campos e acoes."""

    REQUIRED_MARKERS = {"{{COMPRADOR}}", "{{CPF_CNPJ}}", "{{VENDEDOR}}"}

    def __init__(self, master: ctk.CTkFrame, on_update, callbacks: dict) -> None:
        super().__init__(
            master,
            fg_color=COLORS["bg2"],
            corner_radius=0,
            border_width=0,
        )
        self.on_update = on_update
        self.callbacks = callbacks
        self.entries: dict[str, ctk.CTkEntry] = {}
        self.error_labels: dict[str, ctk.CTkLabel] = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_content()

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
            text="Preencha os Dados",
            text_color=COLORS["text"],
            font=font(13, "bold"),
            anchor="w",
        ).grid(row=0, column=1, sticky="ew")

    def _build_content(self) -> None:
        self.content = ctk.CTkScrollableFrame(
            self,
            fg_color=COLORS["bg2"],
            corner_radius=0,
            scrollbar_fg_color=COLORS["bg2"],
            scrollbar_button_color="#64748B",
            scrollbar_button_hover_color=COLORS["text3"],
        )
        self.content.grid(row=1, column=0, sticky="nsew", padx=(10, 12), pady=(0, 10))
        self.content.grid_columnconfigure(0, weight=1)

        self._build_buyer_card(0)
        self._build_property_card(1)
        self._build_seller_card(2)
        self._build_document_card(3)
        self._build_actions_card(4)

    def _build_buyer_card(self, row: int) -> None:
        card = CollapsibleCard(self.content, "Dados do Comprador", "♙")
        card.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        self._two_col_row(card.body, 0)
        self._add_field(card.body, 0, 0, "Nome Completo", "{{COMPRADOR}}", "Digite o nome completo", columnspan=2)
        self._add_field(card.body, 1, 0, "Nacionalidade", "{{NACIONALIDADE}}", "Digite a nacionalidade")
        self._add_field(card.body, 1, 1, "Profissão", "{{PROFISSAO}}", "Digite a profissão")
        self._add_field(card.body, 2, 0, "Estado Civil", "{{ESTADO_CIVIL}}", "Digite o estado civil")
        self._add_field(card.body, 2, 1, "CPF/CNPJ", "{{CPF_CNPJ}}", "Digite o CPF ou CNPJ")

    def _build_property_card(self, row: int) -> None:
        card = CollapsibleCard(self.content, "Dados do Imóvel", "▦")
        card.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        self._two_col_row(card.body, 0)
        self._add_field(card.body, 0, 0, "Lote/Unidade", "{{LOTE}}", "Ex.: 04 ou 1203")
        self._add_field(card.body, 0, 1, "Quadra", "{{QUADRA}}", "Ex.: 08B")
        self._add_field(card.body, 1, 0, "Empreendimento", "{{EMPREENDIMENTO}}", "Ex.: Alphaville Ribeirão Preto", columnspan=2)

    def _build_seller_card(self, row: int) -> None:
        card = CollapsibleCard(self.content, "Dados do Vendedor", "♙")
        card.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        self._two_col_row(card.body, 0)
        self._add_field(card.body, 0, 0, "Nome do Vendedor", "{{VENDEDOR}}", "Digite o nome do vendedor", columnspan=2)

    def _build_document_card(self, row: int) -> None:
        card = CollapsibleCard(self.content, "Dados do Documento", "▤")
        card.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        self._two_col_row(card.body, 0)
        self._add_field(card.body, 0, 0, "Cidade", "{{CIDADE}}", "Ex.: Ribeirão Preto")
        self._add_field(card.body, 0, 1, "Data", "{{DATA}}", "Ex.: 15 de Junho de 2026", with_today=True)

    def _build_actions_card(self, row: int) -> None:
        card = ctk.CTkFrame(
            self.content,
            fg_color=COLORS["bg2"],
            corner_radius=8,
            border_width=1,
            border_color=COLORS["border2"],
        )
        card.grid(row=row, column=0, sticky="ew", pady=(2, 0))
        card.grid_columnconfigure(0, weight=1, uniform="actions")
        card.grid_columnconfigure(1, weight=1, uniform="actions")

        ctk.CTkLabel(
            card,
            text="AÇÕES",
            text_color=COLORS["green3"],
            font=font(11, "bold"),
            anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 8))

        self._action_button(card, 1, 0, "Selecionar Template", "▣", self.callbacks.get("select_template"))
        self._action_button(card, 1, 1, "Pasta de Saída", "▰", self.callbacks.get("select_output"))
        self._action_button(
            card,
            2,
            0,
            "Gerar Documento",
            "✓",
            self.callbacks.get("generate"),
            columnspan=2,
            fg=COLORS["green2"],
            hover=COLORS["green"],
        )
        self._action_button(
            card,
            3,
            0,
            "Limpar Campos",
            "⌫",
            self.callbacks.get("clear"),
            columnspan=2,
            fg=COLORS["bg4"],
            hover=COLORS["red"],
        )

    def _action_button(
        self,
        parent,
        row: int,
        column: int,
        text: str,
        icon: str,
        command,
        columnspan: int = 1,
        fg: str = COLORS["bg4"],
        hover: str = COLORS["green2"],
    ) -> None:
        ctk.CTkButton(
            parent,
            text=f"{icon}  {text}",
            height=36,
            fg_color=fg,
            hover_color=hover,
            text_color=COLORS["text"],
            border_width=1,
            border_color=COLORS["border2"],
            corner_radius=6,
            font=font(11, "bold"),
            command=command,
        ).grid(
            row=row,
            column=column,
            columnspan=columnspan,
            sticky="ew",
            padx=(10 if column == 0 else 4, 10 if column + columnspan >= 2 else 4),
            pady=(0, 8 if row < 3 else 10),
        )

    def _two_col_row(self, parent, row: int) -> None:
        parent.grid_columnconfigure(0, weight=1, uniform=f"fields-{row}")
        parent.grid_columnconfigure(1, weight=1, uniform=f"fields-{row}")

    def _add_field(
        self,
        parent,
        row: int,
        column: int,
        label: str,
        marker: str,
        placeholder: str,
        columnspan: int = 1,
        with_today: bool = False,
    ) -> None:
        field = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        field.grid(
            row=row,
            column=column,
            columnspan=columnspan,
            sticky="ew",
            padx=(0 if column == 0 else 6, 0),
            pady=(0, 8),
        )
        field.grid_columnconfigure(0, weight=1)

        label_row = ctk.CTkFrame(field, fg_color="transparent", corner_radius=0)
        label_row.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        label_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            label_row,
            text=self._label_text(label),
            text_color=COLORS["text3"],
            font=font(9, "bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        if marker in self.REQUIRED_MARKERS:
            ctk.CTkLabel(
                label_row,
                text=" *",
                text_color=COLORS["red"],
                font=font(9, "bold"),
                anchor="w",
            ).grid(row=0, column=1, sticky="w")

        input_row = ctk.CTkFrame(field, fg_color="transparent", corner_radius=0)
        input_row.grid(row=1, column=0, sticky="ew")
        input_row.grid_columnconfigure(0, weight=1)

        entry = ctk.CTkEntry(input_row, placeholder_text=placeholder, **FIELD_STYLE)
        entry.grid(row=0, column=0, sticky="ew")
        entry.bind("<KeyRelease>", lambda event=None, _marker=marker: self._handle_key_update(_marker))
        self.entries[marker] = entry

        if with_today:
            ctk.CTkButton(
                input_row,
                text="Hoje",
                width=52,
                height=30,
                fg_color=COLORS["bg4"],
                hover_color=COLORS["green2"],
                text_color=COLORS["green4"],
                border_width=1,
                border_color=COLORS["border2"],
                corner_radius=5,
                font=font(10, "bold"),
                command=self._fill_today,
            ).grid(row=0, column=1, padx=(6, 0))

        error = ctk.CTkLabel(
            field,
            text="",
            text_color=COLORS["red"],
            font=font(9),
            anchor="w",
        )
        error.grid(row=2, column=0, sticky="ew", pady=(2, 0))
        self.error_labels[marker] = error

    @staticmethod
    def _label_text(label: str) -> str:
        return " ".join(label.upper()) if len(label) <= 14 else label.upper()

    def _notify_update(self) -> None:
        if self.on_update:
            self.on_update()

    def _handle_key_update(self, marker: str) -> None:
        if marker in self.REQUIRED_MARKERS:
            self.entries[marker].configure(border_color=COLORS["border3"])
            self.error_labels[marker].configure(text="")
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
            if marker in missing:
                self.entries[marker].configure(border_color=COLORS["red"])
                self.error_labels[marker].configure(text="Campo obrigatório")
            else:
                self.entries[marker].configure(border_color=COLORS["border3"])
                self.error_labels[marker].configure(text="")

    def clear_validation(self) -> None:
        for marker, entry in self.entries.items():
            entry.configure(border_color=COLORS["border3"])
            error = self.error_labels.get(marker)
            if error is not None:
                error.configure(text="")

    def set_template_info(self, text: str) -> None:
        return None

    def set_output_info(self, text: str) -> None:
        return None

    def clear(self) -> None:
        for entry in self.entries.values():
            entry.delete(0, "end")
        self.clear_validation()
        self._notify_update()
