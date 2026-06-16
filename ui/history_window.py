from __future__ import annotations

from pathlib import Path
from typing import Any, Callable
from tkinter import BooleanVar

import customtkinter as ctk

from services.template_semantic_analyzer import FIELD_LABELS
from ui.i18n import t
from ui.theme import COLORS, font


class HistoryWindow(ctk.CTkToplevel):
    def __init__(
        self,
        master,
        history_manager,
        callbacks: dict[str, Callable[[dict[str, Any]], None] | Callable[[dict[str, Any], bool], None] | Callable[[], None]],
        session_store=None,
    ) -> None:
        super().__init__(master)
        self.history_manager = history_manager
        self.callbacks = callbacks
        self.session_store = session_store
        self.records: list[dict[str, Any]] = []
        self.selected_record_id: str | None = None

        self.title(t("history_title"))
        self.geometry("1200x760")
        self.minsize(980, 640)
        self.configure(fg_color=COLORS["bg"])
        self.protocol("WM_DELETE_WINDOW", self.withdraw)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_body()
        self.refresh()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color=COLORS["bg"], corner_radius=0)
        header.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 10))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header,
            text=t("history_title"),
            text_color=COLORS["green3"],
            font=font(22, "bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            header,
            text=t("history_subtitle"),
            text_color=COLORS["text3"],
            font=font(10),
            anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        ctk.CTkButton(
            header,
            text=t("history_refresh"),
            width=120,
            height=30,
            fg_color=COLORS["bg4"],
            hover_color=COLORS["green2"],
            text_color=COLORS["text2"],
            corner_radius=6,
            command=self.refresh,
        ).grid(row=0, column=2, rowspan=2, sticky="e")

    def _build_body(self) -> None:
        body = ctk.CTkFrame(self, fg_color=COLORS["bg2"], corner_radius=8, border_width=1, border_color=COLORS["border2"])
        body.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 18))
        body.grid_columnconfigure(0, weight=38, minsize=360)
        body.grid_columnconfigure(1, weight=62, minsize=520)
        body.grid_rowconfigure(1, weight=1)

        self._build_filters(body)
        self._build_list(body)
        self._build_detail(body)

    def _build_filters(self, master: ctk.CTkFrame) -> None:
        filters = ctk.CTkFrame(master, fg_color=COLORS["bg3"], corner_radius=8, border_width=1, border_color=COLORS["border2"])
        filters.grid(row=0, column=0, columnspan=2, sticky="ew", padx=14, pady=(14, 10))
        for column in range(8):
            filters.grid_columnconfigure(column, weight=1 if column in (1, 3, 5, 7) else 0)

        self.search_entry = ctk.CTkEntry(filters, placeholder_text=t("history_search"), fg_color=COLORS["input"], border_color=COLORS["border3"], text_color=COLORS["text"])
        self.search_entry.grid(row=0, column=0, columnspan=2, sticky="ew", padx=(12, 6), pady=(12, 8))

        self.template_entry = ctk.CTkEntry(filters, placeholder_text=t("history_template_filter"), fg_color=COLORS["input"], border_color=COLORS["border3"], text_color=COLORS["text"])
        self.template_entry.grid(row=0, column=2, columnspan=2, sticky="ew", padx=6, pady=(12, 8))

        self.date_from_entry = ctk.CTkEntry(filters, placeholder_text=t("history_date_from"), fg_color=COLORS["input"], border_color=COLORS["border3"], text_color=COLORS["text"])
        self.date_from_entry.grid(row=0, column=4, sticky="ew", padx=6, pady=(12, 8))

        self.date_to_entry = ctk.CTkEntry(filters, placeholder_text=t("history_date_to"), fg_color=COLORS["input"], border_color=COLORS["border3"], text_color=COLORS["text"])
        self.date_to_entry.grid(row=0, column=5, sticky="ew", padx=6, pady=(12, 8))

        self.favorites_only_var = BooleanVar(value=False)
        favorites = ctk.CTkCheckBox(
            filters,
            text=t("history_favorites_only"),
            variable=self.favorites_only_var,
            text_color=COLORS["text2"],
            checkbox_width=18,
            checkbox_height=18,
            border_width=1,
            corner_radius=4,
            fg_color=COLORS["green"],
            hover_color=COLORS["green2"],
        )
        favorites.grid(row=0, column=6, sticky="w", padx=6, pady=(12, 8))

        ctk.CTkButton(
            filters,
            text=t("history_apply_filters"),
            width=120,
            height=30,
            fg_color=COLORS["green"],
            hover_color=COLORS["green2"],
            command=self.refresh,
        ).grid(row=0, column=7, sticky="e", padx=(6, 12), pady=(12, 8))

    def _build_list(self, master: ctk.CTkFrame) -> None:
        left = ctk.CTkFrame(master, fg_color=COLORS["bg3"], corner_radius=8, border_width=1, border_color=COLORS["border2"])
        left.grid(row=1, column=0, sticky="nsew", padx=(14, 10), pady=(0, 14))
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(left, text=t("history_documents"), text_color=COLORS["green3"], font=font(14, "bold"), anchor="w").grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 6))

        self.list_frame = ctk.CTkScrollableFrame(
            left,
            fg_color=COLORS["input"],
            corner_radius=6,
            border_width=1,
            border_color=COLORS["border3"],
        )
        self.list_frame.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))

    def _build_detail(self, master: ctk.CTkFrame) -> None:
        right = ctk.CTkFrame(master, fg_color=COLORS["bg3"], corner_radius=8, border_width=1, border_color=COLORS["border2"])
        right.grid(row=1, column=1, sticky="nsew", padx=(10, 14), pady=(0, 14))
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(right, text=t("history_detail"), text_color=COLORS["green3"], font=font(14, "bold"), anchor="w").grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 6))
        self.detail_text = ctk.CTkTextbox(right, fg_color=COLORS["input"], text_color=COLORS["text"], border_width=1, border_color=COLORS["border3"], font=font(11))
        self.detail_text.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 10))
        self.detail_text.configure(state="disabled")

        actions = ctk.CTkFrame(right, fg_color="transparent", corner_radius=0)
        actions.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 14))
        actions.grid_columnconfigure(0, weight=1)
        actions.grid_columnconfigure(1, weight=1)
        actions.grid_columnconfigure(2, weight=1)

        self.favorite_button = ctk.CTkButton(actions, text=t("history_favorite"), fg_color=COLORS["bg4"], hover_color=COLORS["green2"], text_color=COLORS["text2"], command=self._toggle_favorite)
        self.favorite_button.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ctk.CTkButton(actions, text=t("history_open_document"), fg_color=COLORS["green"], hover_color=COLORS["green2"], command=self._open_document).grid(row=0, column=1, sticky="ew", padx=6)
        ctk.CTkButton(actions, text=t("history_open_folder"), fg_color=COLORS["bg4"], hover_color=COLORS["green2"], text_color=COLORS["text2"], command=self._open_folder).grid(row=0, column=2, sticky="ew", padx=(6, 0))
        ctk.CTkButton(actions, text=t("history_reuse_data"), fg_color=COLORS["bg4"], hover_color=COLORS["green2"], text_color=COLORS["text2"], command=self._reuse_data).grid(row=1, column=0, sticky="ew", padx=(0, 6), pady=(8, 0))
        ctk.CTkButton(actions, text=t("history_duplicate_fill"), fg_color=COLORS["bg4"], hover_color=COLORS["green2"], text_color=COLORS["text2"], command=self._duplicate_fill).grid(row=1, column=1, columnspan=2, sticky="ew", padx=(6, 0), pady=(8, 0))

    def refresh(self) -> None:
        query = self.search_entry.get().strip() if hasattr(self, "search_entry") else ""
        template = self.template_entry.get().strip() if hasattr(self, "template_entry") else ""
        date_from = self.date_from_entry.get().strip() if hasattr(self, "date_from_entry") else ""
        date_to = self.date_to_entry.get().strip() if hasattr(self, "date_to_entry") else ""
        favorites_only = bool(self.favorites_only_var.get()) if hasattr(self, "favorites_only_var") else False
        self.records = self.history_manager.query_records(
            search=query,
            template_name=template,
            date_from=date_from,
            date_to=date_to,
            favorites_only=favorites_only,
        )
        self._render_records()

    def _render_records(self) -> None:
        for child in self.list_frame.winfo_children():
            child.destroy()

        if not self.records:
            ctk.CTkLabel(self.list_frame, text=t("history_empty"), text_color=COLORS["text3"], font=font(11), anchor="w").grid(row=0, column=0, sticky="ew", padx=10, pady=10)
            self.selected_record_id = None
            self._render_detail(None)
            return

        for index, record in enumerate(self.records):
            row = ctk.CTkFrame(self.list_frame, fg_color=COLORS["bg4"] if record.get("id") != self.selected_record_id else COLORS["green2"], corner_radius=6)
            row.grid(row=index, column=0, sticky="ew", padx=8, pady=(8 if index == 0 else 0, 8))
            row.grid_columnconfigure(0, weight=1)
            row.bind("<Button-1>", lambda _e, item=record: self.select_record(item))

            title = f"{'★ ' if record.get('favorite') else ''}{record.get('document_name') or record.get('template_name') or t('history_unknown')}"
            ctk.CTkLabel(row, text=title, text_color=COLORS["text"], font=font(11, "bold"), anchor="w").grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 2))
            subtitle = f"{record.get('template_name', '')} | {record.get('timestamp', '')}"
            ctk.CTkLabel(row, text=subtitle, text_color=COLORS["text3"], font=font(9), anchor="w").grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 8))

        if self.selected_record_id is None and self.records:
            self.select_record(self.records[0])
        else:
            self._render_detail(self.history_manager.get_record(self.selected_record_id) if self.selected_record_id else None)

    def select_record(self, record: dict[str, Any]) -> None:
        self.selected_record_id = str(record.get("id"))
        self._render_records()

    def _render_detail(self, record: dict[str, Any] | None) -> None:
        if self.detail_text is None:
            return
        if not record:
            self._set_detail_text(t("history_no_selection"))
            self.favorite_button.configure(state="disabled")
            return
        fields = record.get("fields", {})
        detected = record.get("detected_fields", {})
        lines = [
            f"{t('history_detail_template')}: {record.get('template_name', '-')}",
            f"{t('history_detail_document')}: {record.get('document_name', '-')}",
            f"{t('history_detail_output')}: {record.get('output_file', '-')}",
            f"{t('history_detail_timestamp')}: {record.get('timestamp', '-')}",
            f"{t('history_detail_profile')}: {record.get('profile_used', '-') or '-'}",
            "",
            t("history_detail_fields"),
        ]
        if isinstance(fields, dict):
            for key, value in fields.items():
                lines.append(f"- {FIELD_LABELS.get(key, key)}: {value}")
        lines.append("")
        lines.append(t("history_detail_detected"))
        if isinstance(detected, dict):
            for key, value in detected.items():
                if isinstance(value, dict):
                    detected_value = value.get("value", "-")
                    confidence = value.get("confidence")
                    source = value.get("source", "")
                    detail = f"{detected_value}"
                    if confidence is not None:
                        detail += f" | {int(round(float(confidence) * 100))}%"
                    if source:
                        detail += f" | {source}"
                    lines.append(f"- {FIELD_LABELS.get(key, key)}: {detail}")
                else:
                    lines.append(f"- {FIELD_LABELS.get(key, key)}: {value}")
        self._set_detail_text("\n".join(lines))
        self.favorite_button.configure(state="normal", text=t("history_unfavorite") if record.get("favorite") else t("history_favorite"))

    def _set_detail_text(self, value: str) -> None:
        self.detail_text.configure(state="normal")
        self.detail_text.delete("1.0", "end")
        self.detail_text.insert("1.0", value)
        self.detail_text.configure(state="disabled")

    def _current_record(self) -> dict[str, Any] | None:
        if not self.selected_record_id:
            return None
        return self.history_manager.get_record(self.selected_record_id)

    def _toggle_favorite(self) -> None:
        record = self._current_record()
        if not record:
            return
        changed = self.history_manager.set_favorite(record["id"], not bool(record.get("favorite")))
        if changed:
            self.refresh()

    def _open_document(self) -> None:
        record = self._current_record()
        if not record:
            return
        callback = self.callbacks.get("open_document")
        if callback:
            callback(record)

    def _open_folder(self) -> None:
        record = self._current_record()
        if not record:
            return
        callback = self.callbacks.get("open_folder")
        if callback:
            callback(record)

    def _reuse_data(self) -> None:
        record = self._current_record()
        if not record:
            return
        callback = self.callbacks.get("reuse_data")
        if callback:
            callback(record)

    def _duplicate_fill(self) -> None:
        record = self._current_record()
        if not record:
            return
        callback = self.callbacks.get("duplicate_fill")
        if callback:
            callback(record)
