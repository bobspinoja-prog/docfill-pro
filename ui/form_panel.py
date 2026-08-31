from datetime import date

import customtkinter as ctk

from services.history_suggestions import HistorySuggestion
from ui.i18n import field_label, t
from ui.symbol_manager import SymbolManager
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
        self.detection_labels: dict[str, ctk.CTkLabel] = {}
        self.suggestion_frames: dict[str, ctk.CTkFrame] = {}
        self.suggestion_labels: dict[str, ctk.CTkLabel] = {}
        self.suggestion_apply_buttons: dict[str, ctk.CTkButton] = {}
        self.suggestion_ignore_buttons: dict[str, ctk.CTkButton] = {}
        self.auto_detected_markers: set[str] = set()
        self.sidebar_symbol_image = SymbolManager.get_symbol("sidebar", size=28)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_content()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color=COLORS["bg2"], corner_radius=0)
        header.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 8))
        header.grid_columnconfigure(1, weight=1)

        if self.sidebar_symbol_image is not None:
            ctk.CTkLabel(
                header,
                image=self.sidebar_symbol_image,
                text="",
                width=30,
                fg_color="transparent",
            ).grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(2, 0))
        else:
            ctk.CTkLabel(
                header,
                text="▤",
                width=22,
                text_color=COLORS["green3"],
                font=symbol_font(18, "bold"),
            ).grid(row=0, column=0, sticky="w", padx=(0, 8))

        ctk.CTkLabel(
            header,
            text=t("form_header"),
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
        card = CollapsibleCard(self.content, t("fields_title"), "♙")
        card.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        self._two_col_row(card.body, 0)
        self._add_field(card.body, 0, 0, field_label("{{COMPRADOR}}"), "{{COMPRADOR}}", t("placeholder_name"), columnspan=2)
        self._add_field(card.body, 1, 0, field_label("{{NACIONALIDADE}}"), "{{NACIONALIDADE}}", t("placeholder_nationality"))
        self._add_field(card.body, 1, 1, field_label("{{PROFISSAO}}"), "{{PROFISSAO}}", t("placeholder_profession"))
        self._add_field(card.body, 2, 0, field_label("{{ESTADO_CIVIL}}"), "{{ESTADO_CIVIL}}", t("placeholder_marital_status"))
        self._add_field(card.body, 2, 1, field_label("{{CPF_CNPJ}}"), "{{CPF_CNPJ}}", t("placeholder_cpf"))

    def _build_property_card(self, row: int) -> None:
        card = CollapsibleCard(self.content, t("property_title"), "▦")
        card.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        self._two_col_row(card.body, 0)
        self._add_field(card.body, 0, 0, field_label("{{LOTE}}"), "{{LOTE}}", t("placeholder_lote"))
        self._add_field(card.body, 0, 1, field_label("{{QUADRA}}"), "{{QUADRA}}", t("placeholder_quadra"))
        self._add_field(card.body, 1, 0, field_label("{{EMPREENDIMENTO}}"), "{{EMPREENDIMENTO}}", t("placeholder_empreendimento"), columnspan=2)

    def _build_seller_card(self, row: int) -> None:
        card = CollapsibleCard(self.content, t("seller_title"), "♙")
        card.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        self._two_col_row(card.body, 0)
        self._add_field(card.body, 0, 0, field_label("{{VENDEDOR}}"), "{{VENDEDOR}}", t("placeholder_vendedor"), columnspan=2)

    def _build_document_card(self, row: int) -> None:
        card = CollapsibleCard(self.content, t("document_title"), "▤")
        card.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        self._two_col_row(card.body, 0)
        self._add_field(card.body, 0, 0, field_label("{{CIDADE}}"), "{{CIDADE}}", t("placeholder_city"))
        self._add_field(card.body, 0, 1, field_label("{{DATA}}"), "{{DATA}}", t("placeholder_date"), with_today=True)

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
            text=t("actions_title"),
            text_color=COLORS["green3"],
            font=font(11, "bold"),
            anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 8))

        self._action_button(card, 1, 0, t("btn_select_template"), "▣", self.callbacks.get("select_template"))
        self._action_button(card, 1, 1, t("btn_output_folder"), "▰", self.callbacks.get("select_output"))
        self._action_button(
            card,
            2,
            0,
            t("btn_generate"),
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
            "Reescrever Template",
            "M",
            self.callbacks.get("rewrite_template"),
            columnspan=2,
            fg=COLORS["bg4"],
            hover=COLORS["green2"],
        )
        self._action_button(
            card,
            4,
            0,
            "Limpar areas PDF",
            "P",
            self.callbacks.get("clear_pdf_areas"),
            columnspan=2,
            fg=COLORS["bg4"],
            hover=COLORS["border3"],
        )
        self._action_button(
            card,
            5,
            0,
            t("btn_clear"),
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
                text=t("btn_today"),
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

        detection = ctk.CTkLabel(
            field,
            text="",
            text_color=COLORS["green4"],
            font=font(9),
            anchor="w",
        )
        detection.grid(row=3, column=0, sticky="ew", pady=(1, 0))
        self.detection_labels[marker] = detection

        suggestion = ctk.CTkFrame(field, fg_color="transparent", corner_radius=0)
        suggestion.grid(row=4, column=0, sticky="ew", pady=(2, 0))
        suggestion.grid_columnconfigure(0, weight=1)
        suggestion.grid_columnconfigure(1, weight=0)
        suggestion.grid_columnconfigure(2, weight=0)
        suggestion.grid_remove()
        self.suggestion_frames[marker] = suggestion

        suggestion_label = ctk.CTkLabel(
            suggestion,
            text="",
            text_color=COLORS["text3"],
            font=font(9),
            anchor="w",
            justify="left",
            wraplength=280,
        )
        suggestion_label.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.suggestion_labels[marker] = suggestion_label

        apply_button = ctk.CTkButton(
            suggestion,
            text=t("history_suggestion_apply"),
            width=66,
            height=22,
            fg_color=COLORS["green2"],
            hover_color=COLORS["green"],
            text_color=COLORS["text"],
            font=font(9, "bold"),
            corner_radius=5,
        )
        apply_button.grid(row=0, column=1, sticky="e", padx=(0, 4))
        self.suggestion_apply_buttons[marker] = apply_button

        ignore_button = ctk.CTkButton(
            suggestion,
            text=t("history_suggestion_ignore"),
            width=66,
            height=22,
            fg_color=COLORS["bg4"],
            hover_color=COLORS["border3"],
            text_color=COLORS["text2"],
            font=font(9, "bold"),
            corner_radius=5,
        )
        ignore_button.grid(row=0, column=2, sticky="e")
        self.suggestion_ignore_buttons[marker] = ignore_button

    @staticmethod
    def _label_text(label: str) -> str:
        return " ".join(label.upper()) if len(label) <= 14 else label.upper()

    def _notify_update(self) -> None:
        if self.on_update:
            self.on_update()

    def _handle_key_update(self, marker: str) -> None:
        self.clear_detected_indicator(marker)
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
        self.clear_detected_indicator("{{DATA}}")
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
            self.clear_detected_indicator(marker)
            updated += 1
        if updated:
            self.clear_validation()
            self._notify_update()
        return updated

    def set_detected_values(self, detections: dict, only_empty: bool = True) -> int:
        updated = 0
        for marker, detection in detections.items():
            value = getattr(detection, "value", "")
            confidence = float(getattr(detection, "confidence", 0.0) or 0.0)
            if not value:
                continue
            if confidence < 0.60:
                continue
            if self.set_field_value(
                marker,
                str(value),
                detected=True,
                notify=False,
                only_empty=only_empty,
                confidence=confidence,
            ):
                updated += 1
        if updated:
            self.clear_validation()
            self._notify_update()
        return updated

    def set_field_value(
        self,
        marker: str,
        value: str,
        detected: bool = False,
        notify: bool = True,
        only_empty: bool = False,
        confidence: float | None = None,
    ) -> bool:
        entry = self.entries.get(marker)
        if entry is None:
            return False
        if only_empty and entry.get().strip():
            return False
        entry.delete(0, "end")
        entry.insert(0, str(value))
        if detected:
            self._mark_detected(marker, confidence)
        else:
            self.clear_detected_indicator(marker)
        if notify:
            self.clear_validation()
            self._notify_update()
        return True

    def _mark_detected(self, marker: str, confidence: float | None = None) -> None:
        label = self.detection_labels.get(marker)
        entry = self.entries.get(marker)
        review_needed = confidence is not None and confidence < 0.85
        if label is not None:
            if review_needed:
                label.configure(
                    text=f"revisar detec\u00e7\u00e3o ({int(round(confidence * 100))}%)",
                    text_color=COLORS["yellow"],
                )
            else:
                label.configure(text=t("auto_detected_label"), text_color=COLORS["green4"])
        if entry is not None:
            entry.configure(border_color=COLORS["yellow"] if review_needed else COLORS["border3"])
        self.auto_detected_markers.add(marker)

    def clear_detected_indicator(self, marker: str) -> None:
        label = self.detection_labels.get(marker)
        entry = self.entries.get(marker)
        if label is not None:
            label.configure(text="", text_color=COLORS["green4"])
        if entry is not None:
            entry.configure(border_color=COLORS["border3"])
        self.auto_detected_markers.discard(marker)

    def set_history_suggestion(self, marker: str, suggestion: HistorySuggestion, apply_command, ignore_command) -> None:
        frame = self.suggestion_frames.get(marker)
        label = self.suggestion_labels.get(marker)
        apply_button = self.suggestion_apply_buttons.get(marker)
        ignore_button = self.suggestion_ignore_buttons.get(marker)
        if frame is None or label is None or apply_button is None or ignore_button is None:
            return

        prefix = t("history_suggestion_different") if suggestion.status == "different" else t("history_suggestion_prefix")
        label.configure(text=f"{prefix}: {suggestion.value}")
        apply_button.configure(command=apply_command)
        ignore_button.configure(command=ignore_command)
        frame.grid()

    def clear_history_suggestion(self, marker: str) -> None:
        frame = self.suggestion_frames.get(marker)
        label = self.suggestion_labels.get(marker)
        apply_button = self.suggestion_apply_buttons.get(marker)
        ignore_button = self.suggestion_ignore_buttons.get(marker)
        if label is not None:
            label.configure(text="")
        if apply_button is not None:
            apply_button.configure(command=lambda: None)
        if ignore_button is not None:
            ignore_button.configure(command=lambda: None)
        if frame is not None:
            frame.grid_remove()

    def clear_history_suggestions(self) -> None:
        for marker in list(self.suggestion_frames):
            self.clear_history_suggestion(marker)

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
                self.error_labels[marker].configure(text=t("required_label"))
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
        for marker in list(self.auto_detected_markers):
            self.clear_detected_indicator(marker)
        self.clear_history_suggestions()
        self.clear_validation()
        self._notify_update()
