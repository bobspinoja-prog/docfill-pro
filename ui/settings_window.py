from __future__ import annotations

from pathlib import Path
from tkinter import messagebox
from typing import Any

import customtkinter as ctk

from services.template_semantic_analyzer import FIELD_LABELS, SemanticDetection
from ui.i18n import field_label, t
from ui.theme import COLORS, font


class SettingsWindow(ctk.CTkToplevel):
    """Ajustes: template analysis, semantic field mapping, custom markers,
    and session/history info. Owns only its own widgets; anything that
    mutates app-wide state (accepting a detection, restoring a session, ...)
    is delegated back to the main app instance."""

    def __init__(self, app: Any) -> None:
        super().__init__(app)
        self.app = app

        self.title(t("settings_title"))
        self.geometry("940x840")
        self.minsize(780, 620)
        self.configure(fg_color=COLORS["bg"])
        self.protocol("WM_DELETE_WINDOW", self.withdraw)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.analysis_view: ctk.CTkTextbox | None = None
        self.profile_summary_view: ctk.CTkTextbox | None = None
        self.semantic_rows_frame: ctk.CTkScrollableFrame | None = None
        self.semantic_warning_label: ctk.CTkLabel | None = None
        self.custom_marker: ctk.CTkEntry | None = None
        self.custom_value: ctk.CTkEntry | None = None
        self.mapping_view: ctk.CTkTextbox | None = None
        self.session_history_view: ctk.CTkTextbox | None = None
        self.session_status_label: ctk.CTkLabel | None = None
        self.restore_session_button: ctk.CTkButton | None = None

        self._build_ui()
        self.refresh_all()

    def refresh_all(self) -> None:
        self.refresh_mapping_view()
        self.refresh_template_mapping_view()
        self.refresh_session_views()
        self.analyze_template_section()

    def _build_ui(self) -> None:
        ctk.CTkLabel(
            self,
            text=t("settings_heading"),
            font=font(22, "bold"),
            text_color=COLORS["green3"],
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 4))

        wrapper = ctk.CTkFrame(self, fg_color=COLORS["bg2"], corner_radius=8, border_width=1, border_color=COLORS["border2"])
        wrapper.grid(row=1, column=0, sticky="nsew", padx=18, pady=18)
        wrapper.grid_columnconfigure(0, weight=1)
        wrapper.grid_rowconfigure(3, weight=1)

        analysis_card = ctk.CTkFrame(wrapper, fg_color=COLORS["bg3"], corner_radius=8, border_width=1, border_color=COLORS["border2"])
        analysis_card.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 10))
        analysis_card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(analysis_card, text=t("settings_analysis"), font=font(14, "bold"), text_color=COLORS["green3"], anchor="w").grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 6))
        ctk.CTkButton(analysis_card, text=t("settings_analyze_button"), fg_color=COLORS["green"], hover_color=COLORS["green2"], command=self.analyze_template_section).grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 8))
        self.analysis_view = ctk.CTkTextbox(analysis_card, fg_color=COLORS["input"], text_color=COLORS["text"], border_width=1, border_color=COLORS["border3"], font=font(12), height=150)
        self.analysis_view.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 14))
        self.analysis_view.configure(state="disabled")

        semantic_card = ctk.CTkFrame(wrapper, fg_color=COLORS["bg3"], corner_radius=8, border_width=1, border_color=COLORS["border2"])
        semantic_card.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 10))
        semantic_card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            semantic_card,
            text=t("template_mapping_title"),
            font=font(14, "bold"),
            text_color=COLORS["green3"],
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 6))
        self.profile_summary_view = ctk.CTkTextbox(
            semantic_card,
            fg_color=COLORS["input"],
            text_color=COLORS["text"],
            border_width=1,
            border_color=COLORS["border3"],
            font=font(11),
            height=78,
        )
        self.profile_summary_view.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 10))
        self.profile_summary_view.configure(state="disabled")
        self.semantic_rows_frame = ctk.CTkScrollableFrame(
            semantic_card,
            fg_color=COLORS["input"],
            corner_radius=6,
            border_width=1,
            border_color=COLORS["border3"],
            height=180,
        )
        self.semantic_rows_frame.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 14))
        for column, weight in enumerate((18, 20, 36, 10, 16)):
            self.semantic_rows_frame.grid_columnconfigure(column, weight=weight)

        form_card = ctk.CTkFrame(wrapper, fg_color=COLORS["bg3"], corner_radius=8, border_width=1, border_color=COLORS["border2"])
        form_card.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 10))
        form_card.grid_columnconfigure(0, weight=1)
        form_card.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(form_card, text=t("settings_add_marker"), font=font(14, "bold"), text_color=COLORS["green3"], anchor="w").grid(row=0, column=0, columnspan=2, sticky="ew", padx=14, pady=(12, 6))
        self.custom_marker = ctk.CTkEntry(form_card, placeholder_text=t("custom_marker_placeholder"), fg_color=COLORS["input"], border_color=COLORS["border3"], text_color=COLORS["text"])
        self.custom_marker.grid(row=1, column=0, sticky="ew", padx=(14, 6), pady=(0, 12))
        self.custom_value = ctk.CTkEntry(form_card, placeholder_text=t("custom_value_placeholder"), fg_color=COLORS["input"], border_color=COLORS["border3"], text_color=COLORS["text"])
        self.custom_value.grid(row=1, column=1, sticky="ew", padx=(6, 14), pady=(0, 12))
        ctk.CTkButton(form_card, text=t("settings_save_marker"), fg_color=COLORS["green"], hover_color=COLORS["green2"], command=self.save_mapping).grid(row=2, column=0, columnspan=2, sticky="ew", padx=14, pady=(0, 14))

        list_card = ctk.CTkFrame(wrapper, fg_color=COLORS["bg3"], corner_radius=8, border_width=1, border_color=COLORS["border2"])
        list_card.grid(row=3, column=0, sticky="nsew", padx=14, pady=(0, 14))
        list_card.grid_columnconfigure(0, weight=1)
        list_card.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(list_card, text=t("settings_list_title"), font=font(14, "bold"), text_color=COLORS["green3"], anchor="w").grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 6))
        self.mapping_view = ctk.CTkTextbox(list_card, fg_color=COLORS["input"], text_color=COLORS["text"], border_width=1, border_color=COLORS["border3"], font=font(12))
        self.mapping_view.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
        self.mapping_view.configure(state="disabled")

        session_card = ctk.CTkFrame(wrapper, fg_color=COLORS["bg3"], corner_radius=8, border_width=1, border_color=COLORS["border2"])
        session_card.grid(row=4, column=0, sticky="ew", padx=14, pady=(0, 14))
        session_card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            session_card,
            text=t("settings_session_title"),
            font=font(14, "bold"),
            text_color=COLORS["green3"],
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 6))
        self.session_history_view = ctk.CTkTextbox(
            session_card,
            fg_color=COLORS["input"],
            text_color=COLORS["text"],
            border_width=1,
            border_color=COLORS["border3"],
            font=font(11),
            height=118,
        )
        self.session_history_view.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 8))
        self.session_history_view.configure(state="disabled")
        controls = ctk.CTkFrame(session_card, fg_color="transparent", corner_radius=0)
        controls.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 8))
        controls.grid_columnconfigure(0, weight=1)
        controls.grid_columnconfigure(1, weight=1)
        self.restore_session_button = ctk.CTkButton(
            controls,
            text=t("settings_restore_session"),
            fg_color=COLORS["green"],
            hover_color=COLORS["green2"],
            command=self.app.restore_saved_session,
        )
        self.restore_session_button.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ctk.CTkButton(
            controls,
            text=t("settings_refresh_history"),
            fg_color=COLORS["bg4"],
            hover_color=COLORS["green2"],
            text_color=COLORS["text2"],
            command=self.refresh_session_views,
        ).grid(row=0, column=1, sticky="ew", padx=(6, 0))
        self.session_status_label = ctk.CTkLabel(
            session_card,
            text="",
            text_color=COLORS["text3"],
            font=font(10),
            anchor="w",
            justify="left",
            wraplength=840,
        )
        self.session_status_label.grid(row=3, column=0, sticky="ew", padx=14, pady=(0, 12))

    def analyze_template_section(self) -> None:
        if self.analysis_view is None:
            return
        app = self.app
        if not app.template_path:
            self._set_textbox(self.analysis_view, t("template_status_none"))
            return

        try:
            if app._is_pdf_template():
                handler = app._get_pdf_handler()
                if handler is None:
                    return
                analysis = handler.analyze_template()
                lines = [f"PDF: {analysis['template']}"]
                lines.extend(f"- {item}" for item in analysis["summary"])
                if app.template_suggestions:
                    lines.append(f"- {t('detected_fields_in_text')} {len(app.template_suggestions)}")
                lines.append("")
                lines.append(t("pdf_selectable_areas_label"))
                if analysis["areas"]:
                    lines.extend(f"  - {area}" for area in analysis["areas"])
                else:
                    lines.append(f"  - {t('pdf_no_text_area_detected')}")
                if app.pdf_area_mappings:
                    lines.append("")
                    lines.append(t("pdf_manual_areas_label"))
                    for marker, areas in app.pdf_area_mappings.items():
                        lines.append(f"  - {marker}: {len(areas)} area(s)")
                self._set_textbox(self.analysis_view, "\n".join(lines))
                app._set_status(t("analysis_complete"))
                return

            reader = app._get_reader()
            if reader is None:
                return
            analysis = reader.analyze_template()

            lines = [f"{t('settings_profile_template')}: {analysis['template']}"]
            lines.extend(f"- {item}" for item in analysis["summary"])
            if app.template_suggestions:
                lines.append(f"- {t('detected_fields_in_text')} {len(app.template_suggestions)}")
            lines.append(f"\n{t('detected_markers_label')}")
            if analysis["placeholders"]:
                lines.extend(f"  - {marker}" for marker in analysis["placeholders"])
            else:
                lines.append(f"  - {t('no_markers_found')}")

            lines.append(f"\n{t('identified_areas_label')}")
            if analysis["areas"]:
                lines.extend(f"  - {area}" for area in analysis["areas"])
            else:
                lines.append(f"  - {t('no_special_area_detected')}")

            self._set_textbox(self.analysis_view, "\n".join(lines))
            app._set_status(t("analysis_complete"))
        except Exception as exc:
            self._set_textbox(self.analysis_view, f"{t('template_load_failed')}\n{exc}")
            app._set_status(t("analysis_error"))

    def save_mapping(self) -> None:
        if self.custom_marker is None or self.custom_value is None:
            return
        marker = self.custom_marker.get().strip()
        value = self.custom_value.get().strip()

        try:
            normalized_marker = self.app.mapping_manager.normalize_marker(marker)
            self.app.mapping_manager.add_marker(marker, value)
            self.custom_marker.delete(0, "end")
            self.custom_value.delete(0, "end")
            self.refresh_mapping_view()
            self.app.update_preview()
            messagebox.showinfo(t("mapping_saved"), t("marker_saved_with_name").format(marker=normalized_marker))
        except ValueError as exc:
            messagebox.showerror(t("error_title"), str(exc))

    def refresh_mapping_view(self) -> None:
        if self.mapping_view is None:
            return
        data = self.app.mapping_manager.load()
        lines = [t("mapping_list_empty")] if not data else [f"{key} = {value}" for key, value in sorted(data.items())]
        self._set_textbox(self.mapping_view, "\n".join(lines))

    @staticmethod
    def _ellipsize(value: str, limit: int) -> str:
        text = " ".join((value or "").split())
        if len(text) <= limit:
            return text
        return text[: max(0, limit - 3)].rstrip() + "..."

    @staticmethod
    def _semantic_source_text(detection: SemanticDetection | None) -> str:
        if detection is None:
            return "-"
        parts = [part for part in (detection.source, detection.snippet) if part]
        return " | ".join(parts) if parts else "-"

    def _refresh_template_profile_summary(self) -> None:
        if self.profile_summary_view is None:
            return
        app = self.app
        if not app.template_semantic_hash or not app.template_path:
            self._set_textbox(self.profile_summary_view, t("settings_profile_empty"))
            return

        summary = app.profile_store.summarize(app.template_semantic_hash)
        learned_fields = summary.get("learned_fields", [])
        corrections = summary.get("corrections", [])
        history = summary.get("history", [])
        lines = [
            f"{t('settings_profile_template')}: {summary.get('template_name') or app.template_path.name}",
            f"{t('settings_profile_hash')}: {summary.get('hash', app.template_semantic_hash)[:12]}...",
            f"{t('settings_profile_usage')}: {summary.get('usage_count', 0)}",
            f"{t('settings_profile_fields')}: {len(learned_fields)}",
            f"{t('settings_profile_corrections')}: {len(corrections)}",
        ]
        if learned_fields:
            labels = [field_label(field, FIELD_LABELS.get(field, field)) for field in learned_fields[:6]]
            lines.append(f"{t('settings_profile_learned')}: {', '.join(labels)}")
        if history:
            lines.append(f"{t('settings_profile_last_event')}: {history[-1].get('event', '-')}")
        self._set_textbox(self.profile_summary_view, "\n".join(lines))

    def refresh_session_views(self) -> None:
        if self.session_history_view is None and self.session_status_label is None and self.restore_session_button is None:
            return

        app = self.app
        settings = app.session_store.load()
        recent_templates = app.session_store.recent_templates()
        recent_documents = app.session_store.recent_documents()
        autosave = settings.get("autosave") if isinstance(settings, dict) else None

        history_lines = [t("settings_recent_templates")]
        if recent_templates:
            for item in recent_templates[:5]:
                stamp = item.get("updated_at", "") or item.get("last_used_at", "")
                history_lines.append(f"- {item.get('template_name', '-')}" + (f" | {stamp}" if stamp else ""))
        else:
            history_lines.append(f"- {t('settings_history_empty')}")

        history_lines.append("")
        history_lines.append(t("settings_recent_documents"))
        if recent_documents:
            for item in recent_documents[:5]:
                stamp = item.get("updated_at", "")
                output_name = Path(str(item.get("output_file", "-"))).name
                history_lines.append(f"- {output_name}" + (f" | {stamp}" if stamp else ""))
        else:
            history_lines.append(f"- {t('settings_history_empty')}")

        history_lines.append("")
        if autosave:
            history_lines.append(t("settings_autosave_title"))
            history_lines.append(f"- {autosave.get('template_name') or '-'}")
            if autosave.get("updated_at"):
                history_lines.append(f"- {t('settings_last_saved')}: {autosave['updated_at']}")
        else:
            history_lines.append(t("settings_autosave_empty"))

        self._set_textbox(self.session_history_view, "\n".join(history_lines))

        if self.session_status_label is not None:
            log_path = app.event_logger.base_dir
            text = f"{t('settings_logs_path')}: {log_path}"
            if autosave and autosave.get("template_path"):
                text += f"\n{t('settings_autosave_path')}: {autosave.get('template_path')}"
            last_output = settings.get("last_output_folder", "")
            if last_output:
                text += f"\n{t('settings_last_folder')}: {last_output}"
            self.session_status_label.configure(text=text)

        if self.restore_session_button is not None:
            self.restore_session_button.configure(state="normal" if autosave else "disabled")

    def refresh_template_mapping_view(self) -> None:
        if self.semantic_rows_frame is None:
            return
        for child in self.semantic_rows_frame.winfo_children():
            child.destroy()

        if self.semantic_warning_label is not None:
            self.semantic_warning_label.destroy()
            self.semantic_warning_label = None

        self._refresh_template_profile_summary()

        app = self.app
        if not app.template_path or not app.template_semantic_hash:
            ctk.CTkLabel(
                self.semantic_rows_frame,
                text=t("template_mapping_empty"),
                text_color=COLORS["text3"],
                font=font(11),
                anchor="w",
            ).grid(row=0, column=0, columnspan=5, sticky="ew", padx=10, pady=10)
            return

        headers = (
            t("template_mapping_field"),
            t("template_mapping_value"),
            t("template_mapping_source"),
            t("template_mapping_confidence"),
            t("template_mapping_actions"),
        )
        for column, header in enumerate(headers):
            ctk.CTkLabel(
                self.semantic_rows_frame,
                text=header,
                text_color=COLORS["green4"],
                font=font(10, "bold"),
                anchor="w",
            ).grid(row=0, column=column, sticky="ew", padx=8, pady=(8, 4))

        for row, (marker, label) in enumerate(FIELD_LABELS.items(), start=1):
            detection = app.template_semantic_detections.get(marker)
            value = detection.value if detection and detection.value else "-"
            source = self._semantic_source_text(detection)
            confidence = f"{int(round(detection.confidence * 100))}%" if detection and detection.value else "-"

            ctk.CTkLabel(
                self.semantic_rows_frame,
                text=field_label(marker, label),
                text_color=COLORS["text"],
                font=font(10, "bold"),
                anchor="w",
            ).grid(row=row, column=0, sticky="ew", padx=8, pady=4)
            ctk.CTkLabel(
                self.semantic_rows_frame,
                text=self._ellipsize(value, 30),
                text_color=COLORS["text2"],
                font=font(10),
                anchor="w",
            ).grid(row=row, column=1, sticky="ew", padx=8, pady=4)
            ctk.CTkLabel(
                self.semantic_rows_frame,
                text=self._ellipsize(source, 70),
                text_color=COLORS["text3"],
                font=font(9),
                anchor="w",
                wraplength=300,
            ).grid(row=row, column=2, sticky="ew", padx=8, pady=4)
            ctk.CTkLabel(
                self.semantic_rows_frame,
                text=confidence,
                text_color=COLORS["green4"] if confidence != "-" else COLORS["text3"],
                font=font(10, "bold"),
                anchor="w",
            ).grid(row=row, column=3, sticky="ew", padx=8, pady=4)

            actions = ctk.CTkFrame(self.semantic_rows_frame, fg_color="transparent", corner_radius=0)
            actions.grid(row=row, column=4, sticky="ew", padx=8, pady=3)
            actions.grid_columnconfigure(0, weight=1)
            actions.grid_columnconfigure(1, weight=1)
            has_value = bool(detection and detection.value)
            ctk.CTkButton(
                actions,
                text=t("template_mapping_accept"),
                height=24,
                fg_color=COLORS["green2"],
                hover_color=COLORS["green"],
                text_color=COLORS["text"],
                font=font(9, "bold"),
                corner_radius=5,
                state="normal" if has_value else "disabled",
                command=lambda _marker=marker: app.accept_template_detection(_marker),
            ).grid(row=0, column=0, sticky="ew", padx=(0, 4))
            ctk.CTkButton(
                actions,
                text=t("template_mapping_correct"),
                height=24,
                fg_color=COLORS["bg4"],
                hover_color=COLORS["green2"],
                text_color=COLORS["text2"],
                font=font(9, "bold"),
                corner_radius=5,
                command=lambda _marker=marker: app.correct_template_detection(_marker),
            ).grid(row=0, column=1, sticky="ew")

        if app.semantic_generation_warnings:
            self.semantic_warning_label = ctk.CTkLabel(
                self.semantic_rows_frame,
                text="\n".join(app.semantic_generation_warnings[:3]),
                text_color=COLORS["red"],
                font=font(10, "bold"),
                anchor="w",
                justify="left",
                wraplength=760,
            )
            self.semantic_warning_label.grid(row=len(FIELD_LABELS) + 1, column=0, columnspan=5, sticky="ew", padx=10, pady=(10, 10))

    @staticmethod
    def _set_textbox(textbox, value: str) -> None:
        textbox.configure(state="normal")
        textbox.delete("1.0", "end")
        textbox.insert("1.0", value)
        textbox.configure(state="disabled")
