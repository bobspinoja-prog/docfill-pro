from __future__ import annotations

from typing import Any

import customtkinter as ctk

from services.pdf_handler import PDFManualArea
from services.template_semantic_analyzer import FIELD_LABELS
from ui.i18n import field_label, t
from ui.theme import COLORS, font


def open_pdf_area_dialog(
    app: Any,
    page_index: int,
    pdf_rect: tuple[float, float, float, float],
    selected_text: str = "",
) -> None:
    """Opens the small dialog used to map a dragged PDF area to a form field."""
    default_marker = _suggest_marker_for_selection(app, selected_text)
    labels = {f"{field_label(marker, label)} ({marker})": marker for marker, label in FIELD_LABELS.items()}
    default_label = next((label for label, marker in labels.items() if marker == default_marker), next(iter(labels)))

    window = ctk.CTkToplevel(app)
    window.title(t("pdf_area_dialog_title"))
    window.geometry("460x300")
    window.minsize(420, 260)
    window.configure(fg_color=COLORS["bg"])
    window.transient(app)
    window.grab_set()
    window.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(
        window,
        text=t("pdf_area_selected_label"),
        text_color=COLORS["green3"],
        font=font(16, "bold"),
        anchor="w",
    ).grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 6))

    preview_text = " ".join((selected_text or t("pdf_area_no_text")).split())
    if len(preview_text) > 220:
        preview_text = preview_text[:217].rstrip() + "..."
    ctk.CTkLabel(
        window,
        text=preview_text,
        text_color=COLORS["text2"],
        font=font(11),
        anchor="w",
        justify="left",
        wraplength=420,
    ).grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 12))

    marker_choice = ctk.StringVar(value=default_label)
    ctk.CTkOptionMenu(
        window,
        values=list(labels),
        variable=marker_choice,
        fg_color=COLORS["input"],
        button_color=COLORS["green2"],
        button_hover_color=COLORS["green"],
        text_color=COLORS["text"],
        dropdown_fg_color=COLORS["bg3"],
        dropdown_text_color=COLORS["text"],
        dropdown_hover_color=COLORS["bg4"],
    ).grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 14))

    actions = ctk.CTkFrame(window, fg_color="transparent", corner_radius=0)
    actions.grid(row=3, column=0, sticky="ew", padx=16, pady=(4, 16))
    actions.grid_columnconfigure(0, weight=1)
    actions.grid_columnconfigure(1, weight=1)

    def save_area() -> None:
        marker = labels.get(marker_choice.get(), default_marker)
        area = PDFManualArea(
            marker=marker,
            page_index=page_index,
            rect=tuple(float(value) for value in pdf_rect),
            selected_text=selected_text,
        )
        app.pdf_area_mappings.setdefault(marker, []).append(area)
        app._schedule_autosave_snapshot()
        app.update_preview()
        app.analyze_template_section()
        app._set_status(f"{t('pdf_area_marked_status')} {field_label(marker, FIELD_LABELS.get(marker, marker))}")
        window.destroy()

    ctk.CTkButton(
        actions,
        text=t("pdf_area_save_button"),
        fg_color=COLORS["green2"],
        hover_color=COLORS["green"],
        text_color=COLORS["text"],
        command=save_area,
    ).grid(row=0, column=0, sticky="ew", padx=(0, 6))
    ctk.CTkButton(
        actions,
        text=t("close"),
        fg_color=COLORS["bg4"],
        hover_color=COLORS["border3"],
        text_color=COLORS["text2"],
        command=window.destroy,
    ).grid(row=0, column=1, sticky="ew", padx=(6, 0))


def _suggest_marker_for_selection(app: Any, selected_text: str) -> str:
    clean_selection = " ".join((selected_text or "").split()).lower()
    if clean_selection:
        for marker, detection in app.template_semantic_detections.items():
            value = " ".join((getattr(detection, "value", "") or "").split()).lower()
            if value and (value in clean_selection or clean_selection in value):
                return marker
    return "{{COMPRADOR}}"
