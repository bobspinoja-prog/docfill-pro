import os
import sys
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image

from services.history_manager import HistoryManager
from services.history_suggestions import HistorySuggestion, HistorySuggestions
from services.docx_reader import DOCXReader
from services.docx_writer import DOCXWriter
from services.field_extractor import extract_fields, rewrite_template_with_markers
from services.mapping_manager import MappingManager
from services.pdf_handler import PDFHandler, PDFManualArea, pdf_support_available
from services.semantic_replacements import build_safe_semantic_replacements
from services.structured_logger import StructuredLogger
from services.template_profile_store import TemplateProfileStore
from services.template_semantic_analyzer import FIELD_LABELS, SemanticDetection, TemplateSemanticAnalyzer
from services.user_session_store import UserSessionStore
from ui.form_panel import FormPanel
from ui.history_window import HistoryWindow
from ui.i18n import t
from ui.preview_panel import PreviewPanel
from ui.symbol_manager import SymbolManager
from ui.theme import COLORS, font, symbol_font


class DocFillProApp(ctk.CTk):
    """Aplicativo principal DOCFILL PRO."""

    def __init__(self, initial_template: str | Path | None = None, language: str = "pt") -> None:
        super().__init__()

        self.language = language
        from ui.i18n import set_language
        set_language(language)

        self.title("DOCFILL PRO")
        self.geometry("1600x900")
        self.minsize(1300, 800)
        self._set_app_icon()
        self.configure(fg_color=COLORS["bg"])
        self._apply_window_icon()

        self.template_path: Path | None = None
        self.output_folder: Path | None = None
        self.reader: DOCXReader | None = None
        self.pdf_handler: PDFHandler | None = None
        self.template_kind = "docx"
        self.pdf_area_mappings: dict[str, list[PDFManualArea]] = {}
        self.template_placeholders: set[str] = set()
        self.template_suggestions: dict[str, str] = {}
        self.template_semantic_hash: str | None = None
        self.template_semantic_auto_detections: dict[str, SemanticDetection] = {}
        self.template_semantic_detections: dict[str, SemanticDetection] = {}
        self.semantic_generation_warnings: list[str] = []
        self._state_sync_suspended = False
        self.last_safe_semantic_result = None
        self._preview_job: str | None = None
        self._suggestion_job: str | None = None
        self._autosave_job: str | None = None
        self._pulse_job: str | None = None
        self._splash_job: str | None = None
        self._last_history_suggestion_signature: tuple[str, str, str, tuple[str, ...]] | None = None
        self._pulse_state = False
        self.mapping_manager = MappingManager()
        self.semantic_analyzer = TemplateSemanticAnalyzer()
        self.profile_store = TemplateProfileStore()
        self.session_store = UserSessionStore()
        self.history_manager = HistoryManager()
        self.history_suggestions = HistorySuggestions(self.history_manager, self.session_store, self.semantic_analyzer)
        self.event_logger = StructuredLogger()
        self.logo_image = None
        self.splash_symbol_image = None
        self.splash_frame = None
        self.mapping_window = None
        self.history_window = None
        self.about_window = None
        self.analysis_view = None
        self.mapping_view = None
        self.semantic_rows_frame = None
        self.semantic_warning_label = None
        self.profile_summary_view = None
        self.session_history_view = None
        self.session_status_label = None
        self.restore_session_button = None
        self.custom_marker = None
        self.custom_value = None
        self.about_symbol_image = None
        self._ignored_history_suggestions: set[str] = set()
        self._visible_history_suggestions: dict[str, HistorySuggestion] = {}

        self._build_ui()
        self._show_startup_splash()
        self._pulse_dot()
        if initial_template:
            self.load_template(initial_template, show_errors=False)
        else:
            self._maybe_restore_saved_session_on_startup()
        self.protocol("WM_DELETE_WINDOW", self.close_app)

    def _build_ui(self) -> None:
        root = ctk.CTkFrame(self, fg_color=COLORS["bg"], corner_radius=0)
        self.root_frame = root
        root.pack(fill="both", expand=True)
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(2, weight=1)

        self._build_header(root)
        self._build_status_bar(root)
        self._build_body(root)
        self._build_footer(root)

    def _build_header(self, master: ctk.CTkFrame) -> None:
        header = ctk.CTkFrame(master, fg_color=COLORS["bg"], corner_radius=0, height=56)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(2, weight=1)
        header.grid_propagate(False)

        symbol_image = SymbolManager.get_symbol("header", size=22)
        if symbol_image is None:
            symbol_image = self._fallback_header_logo(22)
        if symbol_image is not None:
            self.logo_image = symbol_image
            ctk.CTkLabel(
                header,
                image=self.logo_image,
                text="",
                width=24,
                fg_color="transparent",
            ).grid(row=0, column=0, sticky="w", padx=(16, 8), pady=16)
        else:
            ctk.CTkLabel(
                header,
                text="DF",
                width=24,
                text_color=COLORS["green3"],
                font=font(12, "bold"),
            ).grid(row=0, column=0, sticky="w", padx=(16, 8), pady=16)

        brand = ctk.CTkFrame(header, fg_color="transparent", corner_radius=0)
        brand.grid(row=0, column=1, sticky="w", pady=7)
        brand.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            brand,
            text=t("app_name"),
            text_color=COLORS["text"],
            font=font(15, "bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            brand,
            text=t("tagline"),
            text_color=COLORS["text3"],
            font=font(10),
            anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=(1, 0))

        actions = ctk.CTkFrame(header, fg_color="transparent", corner_radius=0)
        actions.grid(row=0, column=3, sticky="e", padx=(10, 14), pady=12)
        for col, (text, command) in enumerate((
            (t("history"), self.open_history),
            (t("theme"), self.show_theme_info),
            (t("settings"), self.open_settings),
            (t("about"), self.show_about),
        )):
            ctk.CTkButton(
                actions,
                text=text,
                width=72,
                height=28,
                fg_color="transparent",
                hover_color=COLORS["bg4"],
                text_color=COLORS["text2"],
                border_width=1,
                border_color=COLORS["border"],
                corner_radius=6,
                font=font(10),
                command=command,
            ).grid(row=0, column=col, padx=(0 if col == 0 else 6, 0))

    def _build_status_bar(self, master: ctk.CTkFrame) -> None:
        bar = ctk.CTkFrame(master, fg_color=COLORS["bg"], corner_radius=0, height=30)
        bar.grid(row=1, column=0, sticky="ew")
        bar.grid_columnconfigure(7, weight=1)
        bar.grid_rowconfigure(0, weight=1)
        bar.grid_propagate(False)

        self.status_dot = ctk.CTkLabel(bar, text="●", text_color=COLORS["green"], font=symbol_font(12, "bold"))
        self.status_dot.grid(row=0, column=0, padx=(16, 6), sticky="ns")

        self.status_label = ctk.CTkLabel(bar, text=t("ready"), text_color=COLORS["green4"], font=font(11, "bold"))
        self.status_label.grid(row=0, column=1, sticky="w")

        self._separator(bar, 2)

        ctk.CTkLabel(bar, text=t("template"), text_color=COLORS["text3"], font=font(10, "bold")).grid(row=0, column=3, padx=(12, 4), sticky="w")
        self.template_status_label = ctk.CTkLabel(bar, text=t("none"), text_color=COLORS["text2"], font=font(10), anchor="w")
        self.template_status_label.grid(row=0, column=4, sticky="w")

        self._separator(bar, 5)

        ctk.CTkLabel(bar, text=t("output"), text_color=COLORS["text3"], font=font(10, "bold")).grid(row=0, column=6, padx=(12, 4), sticky="w")
        self.output_status_label = ctk.CTkLabel(bar, text=t("no_output"), text_color=COLORS["text2"], font=font(10), anchor="w")
        self.output_status_label.grid(row=0, column=7, sticky="w")

    def _build_body(self, master: ctk.CTkFrame) -> None:
        body = ctk.CTkFrame(master, fg_color=COLORS["bg"], corner_radius=0)
        body.grid(row=2, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=58, minsize=700)
        body.grid_columnconfigure(1, weight=0)
        body.grid_columnconfigure(2, weight=42, minsize=500)
        body.grid_rowconfigure(0, weight=1)

        self.preview_panel = PreviewPanel(
            body,
            on_refresh=self.update_preview,
            on_pdf_area_selected=self.handle_pdf_area_selected,
        )
        self.preview_panel.grid(row=0, column=0, sticky="nsew")

        ctk.CTkFrame(body, fg_color=COLORS["border"], width=1, corner_radius=0).grid(row=0, column=1, sticky="ns")

        self.form_panel = FormPanel(
            body,
            on_update=self.request_preview_update,
            callbacks={
                "select_template": self.select_template,
                "select_output": self.select_output,
                "generate": self.generate_document,
                "rewrite_template": self.rewrite_template_with_markers,
                "clear_pdf_areas": self.clear_pdf_areas,
                "clear": self.clear_form,
            },
        )
        self.form_panel.grid(row=0, column=2, sticky="nsew")

    def _set_app_icon(self) -> None:
        icon_path = self._asset_path("app_icon.ico")
        if icon_path.exists():
            try:
                self.iconbitmap(str(icon_path))
            except Exception:
                pass

    def _show_startup_splash(self) -> None:
        self.splash_symbol_image = SymbolManager.get_symbol("loading", size=64)
        if self.splash_symbol_image is None:
            return

        overlay = ctk.CTkFrame(self.root_frame, fg_color=COLORS["bg"], corner_radius=0)
        overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        overlay.grid_columnconfigure(0, weight=1)
        overlay.grid_rowconfigure(0, weight=1)
        self.splash_frame = overlay

        content = ctk.CTkFrame(overlay, fg_color="transparent", corner_radius=0)
        content.grid(row=0, column=0)
        content.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(content, image=self.splash_symbol_image, text="", fg_color="transparent").grid(row=0, column=0, pady=(0, 16))
        ctk.CTkLabel(
            content,
            text=t("app_name"),
            text_color=COLORS["text"],
            font=font(18, "bold"),
        ).grid(row=1, column=0, pady=(0, 4))
        ctk.CTkLabel(
            content,
            text=t("tagline"),
            text_color=COLORS["text3"],
            font=font(11),
        ).grid(row=2, column=0)

        self._splash_job = self.after(1200, self._hide_startup_splash)

    def _hide_startup_splash(self) -> None:
        self._splash_job = None
        if self.splash_frame is not None:
            self.splash_frame.destroy()
            self.splash_frame = None

    def _fallback_header_logo(self, size: int) -> ctk.CTkImage | None:
        logo_path = self._asset_path("logo.png")
        if not logo_path.exists():
            return None
        try:
            image = Image.open(logo_path).convert("RGBA")
            image.thumbnail((size, size), Image.Resampling.LANCZOS)
            canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            canvas.alpha_composite(image, ((size - image.width) // 2, (size - image.height) // 2))
            return ctk.CTkImage(canvas, size=(size, size))
        except Exception:
            return None

    def _build_footer(self, master: ctk.CTkFrame) -> None:
        footer = ctk.CTkFrame(master, fg_color=COLORS["bg2"], corner_radius=0, height=26)
        footer.grid(row=3, column=0, sticky="ew")
        footer.grid_columnconfigure(1, weight=1)
        footer.grid_propagate(False)

        ctk.CTkLabel(
            footer,
            text=t("app_name") + " v1.2.0",
            text_color=COLORS["text2"],
            font=font(10),
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=14, pady=4)

        status = ctk.CTkFrame(footer, fg_color="transparent", corner_radius=0)
        status.grid(row=0, column=2, sticky="e", padx=14, pady=4)
        self.footer_status_dot = ctk.CTkLabel(status, text="●", text_color=COLORS["green"], font=symbol_font(9))
        self.footer_status_dot.grid(row=0, column=0, sticky="e", padx=(0, 6))
        self.footer_status_label = ctk.CTkLabel(status, text=t("ready"), text_color=COLORS["green4"], font=font(10, "bold"))
        self.footer_status_label.grid(row=0, column=1, sticky="e")

    def open_settings(self) -> None:
        if self.mapping_window is not None and self.mapping_window.winfo_exists():
            self.mapping_window.deiconify()
            self.mapping_window.lift()
            self.refresh_mapping_view()
            self.refresh_template_mapping_view()
            self.refresh_session_views()
            self.analyze_template_section()
            return

        window = ctk.CTkToplevel(self)
        window.title(t("settings_title"))
        window.geometry("940x840")
        window.minsize(780, 620)
        window.configure(fg_color=COLORS["bg"])
        window.protocol("WM_DELETE_WINDOW", window.withdraw)
        window.grid_columnconfigure(0, weight=1)
        window.grid_rowconfigure(1, weight=1)
        self.mapping_window = window

        ctk.CTkLabel(
            window,
            text=t("settings_heading"),
            font=font(22, "bold"),
            text_color=COLORS["green3"],
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 4))

        wrapper = ctk.CTkFrame(window, fg_color=COLORS["bg2"], corner_radius=8, border_width=1, border_color=COLORS["border2"])
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
        self.custom_marker = ctk.CTkEntry(form_card, placeholder_text="Ex.: TELEFONE", fg_color=COLORS["input"], border_color=COLORS["border3"], text_color=COLORS["text"])
        self.custom_marker.grid(row=1, column=0, sticky="ew", padx=(14, 6), pady=(0, 12))
        self.custom_value = ctk.CTkEntry(form_card, placeholder_text="Valor do marcador", fg_color=COLORS["input"], border_color=COLORS["border3"], text_color=COLORS["text"])
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
            command=self.restore_saved_session,
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

        self.refresh_mapping_view()
        self.refresh_template_mapping_view()
        self.refresh_session_views()
        self.analyze_template_section()

    def open_history(self) -> None:
        if self.history_window is not None and self.history_window.winfo_exists():
            self.history_window.deiconify()
            self.history_window.lift()
            self.history_window.refresh()
            return

        window = HistoryWindow(
            self,
            self.history_manager,
            callbacks={
                "open_document": self._history_open_document,
                "open_folder": self._history_open_folder,
                "reuse_data": self._history_reuse_data,
                "duplicate_fill": self._history_duplicate_fill,
            },
            session_store=self.session_store,
        )
        self.history_window = window

    def show_theme_info(self) -> None:
        messagebox.showinfo(t("theme"), t("theme_info"))

    def show_about(self) -> None:
        if self.about_window is not None and self.about_window.winfo_exists():
            self.about_window.deiconify()
            self.about_window.lift()
            return

        window = ctk.CTkToplevel(self)
        window.title(t("about_title"))
        window.geometry("420x280")
        window.resizable(False, False)
        window.configure(fg_color=COLORS["bg"])
        window.grid_columnconfigure(0, weight=1)
        self.about_window = window

        content = ctk.CTkFrame(window, fg_color="transparent", corner_radius=0)
        content.grid(row=0, column=0, sticky="nsew", padx=24, pady=24)
        content.grid_columnconfigure(0, weight=1)

        self.about_symbol_image = SymbolManager.get_symbol("empty", size=72)
        if self.about_symbol_image is not None:
            ctk.CTkLabel(content, image=self.about_symbol_image, text="", fg_color="transparent").grid(row=0, column=0, pady=(0, 14))

        ctk.CTkLabel(
            content,
            text=t("app_name"),
            text_color=COLORS["text"],
            font=font(18, "bold"),
        ).grid(row=1, column=0, pady=(0, 6))

        ctk.CTkLabel(
            content,
            text=t("about_text"),
            text_color=COLORS["text2"],
            font=font(11),
            justify="center",
            wraplength=340,
        ).grid(row=2, column=0, pady=(0, 18))

        ctk.CTkButton(
            content,
            text=t("close"),
            width=120,
            height=32,
            fg_color=COLORS["green2"],
            hover_color=COLORS["green"],
            text_color=COLORS["text"],
            corner_radius=6,
            command=window.withdraw,
        ).grid(row=3, column=0)

    def _history_open_document(self, record: dict[str, str]) -> None:
        output_file = record.get("output_file", "")
        if not output_file:
            return
        path = Path(output_file)
        if path.exists():
            os.startfile(str(path))

    def _history_open_folder(self, record: dict[str, str]) -> None:
        output_file = record.get("output_file", "")
        if not output_file:
            return
        folder = Path(output_file).parent
        if folder.exists():
            os.startfile(str(folder))

    def _history_reuse_data(self, record: dict[str, str]) -> None:
        fields = record.get("fields", {})
        if not isinstance(fields, dict) or not fields:
            messagebox.showinfo(t("history_title"), t("history_no_fields"))
            return
        if not messagebox.askyesno(t("history_title"), t("history_reuse_confirm")):
            return
        template_path = record.get("template_path", "")
        if template_path and Path(template_path).exists():
            self.load_template(template_path, show_errors=False)
        self.form_panel.set_values({str(key): str(value) for key, value in fields.items()}, only_empty=False)
        output_folder = record.get("output_folder", "")
        if output_folder:
            self.output_folder = Path(output_folder)
        self._refresh_status_context()
        self._schedule_autosave_snapshot()
        self.refresh_session_views()
        self._set_status("Dados reutilizados")

    def _history_duplicate_fill(self, record: dict[str, str]) -> None:
        template_path = record.get("template_path", "")
        fields = record.get("fields", {})
        if not template_path or not Path(template_path).exists():
            messagebox.showinfo(t("history_title"), t("history_missing_template"))
            return
        if not messagebox.askyesno(t("history_title"), t("history_duplicate_confirm")):
            return
        self.load_template(template_path, show_errors=False)
        if isinstance(fields, dict):
            self.form_panel.set_values({str(key): str(value) for key, value in fields.items()}, only_empty=False)
        output_folder = record.get("output_folder", "")
        if output_folder:
            self.output_folder = Path(output_folder)
        self._refresh_status_context()
        self._schedule_autosave_snapshot()
        self.refresh_session_views()
        self._set_status("Preenchimento duplicado")

    def apply_history_suggestion(self, marker: str) -> None:
        suggestion = self._visible_history_suggestions.get(marker)
        if suggestion is None:
            return
        self.form_panel.set_field_value(marker, suggestion.value, detected=False)
        self.form_panel.clear_history_suggestion(marker)
        self._visible_history_suggestions.pop(marker, None)
        self._last_history_suggestion_signature = None
        self._schedule_autosave_snapshot()
        self.refresh_session_views()
        self._set_status("Sugestão aplicada")

    def ignore_history_suggestion(self, marker: str) -> None:
        suggestion = self._visible_history_suggestions.get(marker)
        if suggestion is None:
            return
        self._ignored_history_suggestions.add(suggestion.key)
        self.form_panel.clear_history_suggestion(marker)
        self._visible_history_suggestions.pop(marker, None)
        self._last_history_suggestion_signature = None
        self._set_status("Sugestão ignorada")

    def analyze_template_section(self) -> None:
        if self.analysis_view is None:
            return
        if not self.template_path:
            self._set_textbox(self.analysis_view, "Selecione um template .docx para iniciar a análise.")
            return

        try:
            if self._is_pdf_template():
                handler = self._get_pdf_handler()
                if handler is None:
                    return
                analysis = handler.analyze_template()
                lines = [f"PDF: {analysis['template']}"]
                lines.extend(f"- {item}" for item in analysis["summary"])
                if self.template_suggestions:
                    lines.append(f"- Campos detectados no texto: {len(self.template_suggestions)}")
                lines.append("")
                lines.append("Areas selecionaveis:")
                if analysis["areas"]:
                    lines.extend(f"  - {area}" for area in analysis["areas"])
                else:
                    lines.append("  - Nenhuma area de texto detectada.")
                if self.pdf_area_mappings:
                    lines.append("")
                    lines.append("Areas marcadas manualmente:")
                    for marker, areas in self.pdf_area_mappings.items():
                        lines.append(f"  - {marker}: {len(areas)} area(s)")
                self._set_textbox(self.analysis_view, "\n".join(lines))
                self._set_status("Analise PDF concluida")
                return

            reader = self._get_reader()
            if reader is None:
                return
            analysis = reader.analyze_template()

            lines = [f"Template: {analysis['template']}"]
            lines.extend(f"- {item}" for item in analysis["summary"])
            if self.template_suggestions:
                lines.append(f"- Campos detectados no texto: {len(self.template_suggestions)}")
            lines.append("\nMarcadores detectados:")
            if analysis["placeholders"]:
                lines.extend(f"  - {marker}" for marker in analysis["placeholders"])
            else:
                lines.append("  - Nenhum marcador encontrado.")

            lines.append("\nÁreas identificadas:")
            if analysis["areas"]:
                lines.extend(f"  - {area}" for area in analysis["areas"])
            else:
                lines.append("  - Nenhuma área especial detectada.")

            self._set_textbox(self.analysis_view, "\n".join(lines))
            self._set_status("Análise concluída")
        except Exception as exc:
            self._set_textbox(self.analysis_view, f"Não foi possível analisar o template:\n{exc}")
            self._set_status("Erro na análise")

    def update_preview(self) -> None:
        if not self.template_path:
            self.preview_panel.set_model_name(t("preview_none"))
            self.preview_panel.set_marker_count(0)
            self.preview_panel.set_text(t("preview_empty"))
            self._refresh_status_context()
            self._set_status(t("ready"))
            return

        try:
            if self._is_pdf_template():
                handler = self._get_pdf_handler()
                if handler is None:
                    return
                analysis = handler.analyze_template()
                pages = handler.render_pages(self.preview_panel.zoom_percent)
                marker_count = len(analysis["placeholders"]) or len(self.template_suggestions)
                marker_count += len(self._flatten_pdf_areas())
                self.preview_panel.set_model_name(self.template_path.name)
                self.preview_panel.set_marker_count(marker_count)
                self.preview_panel.set_pdf_pages(
                    pages,
                    areas=self._flatten_pdf_areas(),
                    values=self.form_panel.get_values(),
                )
                self._refresh_status_context()
                self._set_status("PDF pronto")
                return

            reader = self._get_reader()
            if reader is None:
                return
            replacements = self._build_replacements()
            text = reader.extract_text(replacements)
            analysis = reader.analyze_template()
            marker_count = len(analysis["placeholders"]) or len(self.template_suggestions)
            self.preview_panel.set_model_name(self.template_path.name)
            self.preview_panel.set_marker_count(marker_count)
            self.preview_panel.set_text(text)
            self._refresh_status_context()
            self._set_status("Pronto")
        except Exception as exc:
            self.preview_panel.set_text(f"Não foi possível gerar o preview: {exc}")
            self.preview_panel.set_marker_count(0)
            self._set_status("Erro no preview")

    def select_template(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Selecionar Template DOCX ou PDF",
            filetypes=[
                ("Documentos suportados", "*.docx *.pdf"),
                ("Word moderno (.docx)", "*.docx"),
                ("PDF (.pdf)", "*.pdf"),
                ("Word antigo (.doc)", "*.doc"),
                ("Todos os arquivos", "*.*"),
            ],
        )
        if file_path:
            self.load_template(file_path)

    def select_output(self) -> None:
        folder = filedialog.askdirectory(title="Selecionar Pasta de Saída")
        if folder:
            self.output_folder = Path(folder)
            self.session_store.set_last_output_folder(self.output_folder)
            self.event_logger.log(
                "output_selected",
                message="Pasta de saída definida",
                output_folder=str(self.output_folder),
            )
            self._schedule_autosave_snapshot()
            self._refresh_status_context()
            self._set_status("Pasta definida")
            self.refresh_session_views()

    def clear_form(self) -> None:
        self.form_panel.clear()
        self.form_panel.clear_history_suggestions()
        self._visible_history_suggestions.clear()
        self._last_history_suggestion_signature = None
        self._schedule_autosave_snapshot()
        self._set_status("Campos limpos")

    def clear_pdf_areas(self) -> None:
        if not self.pdf_area_mappings:
            self._set_status("Nenhuma area PDF marcada")
            return
        self.pdf_area_mappings = {}
        self._schedule_autosave_snapshot()
        self.update_preview()
        self.analyze_template_section()
        self._set_status("Areas PDF limpas")

    def handle_pdf_area_selected(self, page_index: int, pdf_rect: tuple[float, float, float, float], selected_text: str = "") -> None:
        if not self._is_pdf_template():
            return
        default_marker = self._suggest_marker_for_pdf_selection(selected_text)
        labels = {
            f"{label} ({marker})": marker
            for marker, label in FIELD_LABELS.items()
        }
        default_label = next((label for label, marker in labels.items() if marker == default_marker), next(iter(labels)))

        window = ctk.CTkToplevel(self)
        window.title("Marcar area PDF")
        window.geometry("460x300")
        window.minsize(420, 260)
        window.configure(fg_color=COLORS["bg"])
        window.transient(self)
        window.grab_set()
        window.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            window,
            text="Area selecionada",
            text_color=COLORS["green3"],
            font=font(16, "bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 6))

        preview_text = " ".join((selected_text or "Area sem texto detectado").split())
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
            self.pdf_area_mappings.setdefault(marker, []).append(area)
            self._schedule_autosave_snapshot()
            self.update_preview()
            self.analyze_template_section()
            self._set_status(f"Area PDF marcada: {FIELD_LABELS.get(marker, marker)}")
            window.destroy()

        ctk.CTkButton(
            actions,
            text="Salvar marcador",
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

    def _suggest_marker_for_pdf_selection(self, selected_text: str) -> str:
        clean_selection = " ".join((selected_text or "").split()).lower()
        if clean_selection:
            for marker, detection in self.template_semantic_detections.items():
                value = " ".join((getattr(detection, "value", "") or "").split()).lower()
                if value and (value in clean_selection or clean_selection in value):
                    return marker
        return "{{COMPRADOR}}"

    def generate_document(self) -> None:
        if not self.template_path:
            messagebox.showerror("Erro", "Selecione um template .docx ou .pdf antes de gerar o documento.")
            return

        values = self.form_panel.get_values()
        missing = self.form_panel.get_missing_required()
        if missing:
            self.form_panel.mark_missing_required(missing)
            messagebox.showerror("Validação", "Preencha os campos obrigatórios marcados em vermelho.")
            return

        output_folder = self.output_folder
        if output_folder is None:
            selected_folder = filedialog.askdirectory(title="Selecionar Pasta de Saída")
            if not selected_folder:
                return
            output_folder = Path(selected_folder)
            self.output_folder = output_folder
            self._refresh_status_context()

        output_folder = Path(output_folder)
        try:
            output_folder.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            messagebox.showerror("Pasta de saída inválida", f"Não foi possível criar a pasta de saída:\n{exc}")
            self._set_status("Pasta de saída inválida")
            return
        if not output_folder.is_dir():
            messagebox.showerror("Pasta de saída inválida", "O caminho de saída selecionado não é uma pasta.")
            self._set_status("Pasta de saída inválida")
            return

        if self._is_pdf_template():
            self._generate_pdf_document(values, output_folder)
            return

        replacements = self._build_replacements()
        self.refresh_template_mapping_view()
        comprador = values.get("{{COMPRADOR}}", "").strip()
        sanitized_name = self._sanitize_filename(comprador)
        output_path = self._next_available_path(Path(output_folder) / f"DECLARACAO - {sanitized_name}.docx")

        try:
            writer = DOCXWriter()
            writer.generate(self.template_path, output_path, replacements)
            messagebox.showinfo("Sucesso", f"Documento gerado com sucesso em:\n{output_path}")
            self._record_template_profile()
            self._record_template_usage()
            try:
                self.history_manager.record_document(
                    template_name=self.template_path.name,
                    template_hash=self.template_semantic_hash or "",
                    output_file=output_path,
                    document_name=output_path.name,
                    fields=values,
                    detected_fields={
                        marker: detection.to_dict()
                        for marker, detection in self.template_semantic_detections.items()
                        if detection.value
                    },
                    profile_used=self.template_semantic_hash or self.template_path.name,
                    template_path=self.template_path,
                    output_folder=output_folder,
                )
            except Exception as exc:
                self.event_logger.log(
                    "history_record_error",
                    level="warning",
                    message="Falha ao registrar histórico",
                    template_path=str(self.template_path),
                    output_path=str(output_path),
                    error=str(exc),
                )
            if self.template_semantic_hash:
                self.session_store.record_export(self.template_semantic_hash, self.template_path.name, output_path)
                self.profile_store.record_export(self.template_semantic_hash, self.template_path.name, output_path)
            self.event_logger.log(
                "document_generated",
                message="Documento gerado",
                template_path=str(self.template_path),
                template_hash=self.template_semantic_hash,
                output_path=str(output_path),
                safe_replacements=list(replacements.keys()),
                warnings=list(self.semantic_generation_warnings),
            )
            if self.last_safe_semantic_result and self.last_safe_semantic_result.blocked_replacements:
                self.event_logger.log(
                    "semantic_replacements_blocked",
                    message="Substituições semânticas bloqueadas por segurança",
                    template_path=str(self.template_path),
                    template_hash=self.template_semantic_hash,
                    blocked=[item.to_dict() for item in self.last_safe_semantic_result.blocked_replacements],
                    warnings=list(self.last_safe_semantic_result.warnings),
                )
            try:
                self._save_autosave_snapshot()
            except Exception as exc:
                self.event_logger.log(
                    "autosave_save_error",
                    level="warning",
                    message="Falha ao salvar autosave",
                    template_path=str(self.template_path),
                    output_path=str(output_path),
                    error=str(exc),
                )
            self.refresh_session_views()
            if self.semantic_generation_warnings:
                self._set_status("Revisão necessária")
            else:
                self._set_status("Documento gerado")
        except Exception as exc:
            self.event_logger.log(
                "document_generation_error",
                level="error",
                message="Falha ao gerar documento",
                template_path=str(self.template_path),
                output_path=str(output_path),
                error=str(exc),
            )
            messagebox.showerror("Erro ao gerar", f"Não foi possível gerar o arquivo: {exc}")

    def _generate_pdf_document(self, values: dict[str, str], output_folder: Path) -> None:
        handler = self._get_pdf_handler()
        if handler is None or self.template_path is None:
            messagebox.showerror("Erro", "Nao foi possivel ler o PDF atual.")
            return

        comprador = values.get("{{COMPRADOR}}", "").strip()
        sanitized_name = self._sanitize_filename(comprador)
        output_path = self._next_available_path(Path(output_folder) / f"DECLARACAO - {sanitized_name}.pdf")
        try:
            report = handler.generate_filled_pdf(
                output_path,
                values,
                manual_areas=self.pdf_area_mappings,
                detections=self.template_semantic_detections,
            )
            summary = report.to_dict()
            lines = [
                f"PDF gerado com sucesso em:\n{output_path}",
                "",
                f"Areas manuais aplicadas: {len(summary['manual_fields'])}",
                f"Substituicoes detectadas: {len(summary['auto_fields'])}",
                f"Itens ignorados: {len(summary['skipped'])}",
            ]
            if summary["skipped"]:
                lines.append("")
                lines.append("Ignorados:")
                lines.extend(f"- {item}" for item in summary["skipped"][:5])
            if summary["warnings"]:
                lines.append("")
                lines.append("Avisos:")
                lines.extend(f"- {item}" for item in summary["warnings"][:5])
            messagebox.showinfo("Sucesso", "\n".join(lines))
            self._record_template_profile()
            self._record_template_usage()
            try:
                self.history_manager.record_document(
                    template_name=self.template_path.name,
                    template_hash=self.template_semantic_hash or "",
                    output_file=output_path,
                    document_name=output_path.name,
                    fields=values,
                    detected_fields={
                        marker: detection.to_dict()
                        for marker, detection in self.template_semantic_detections.items()
                        if detection.value
                    },
                    profile_used=self.template_semantic_hash or self.template_path.name,
                    template_path=self.template_path,
                    output_folder=output_folder,
                )
            except Exception as exc:
                self.event_logger.log(
                    "history_record_error",
                    level="warning",
                    message="Falha ao registrar historico PDF",
                    template_path=str(self.template_path),
                    output_path=str(output_path),
                    error=str(exc),
                )
            if self.template_semantic_hash:
                self.session_store.record_export(self.template_semantic_hash, self.template_path.name, output_path)
                self.profile_store.record_export(self.template_semantic_hash, self.template_path.name, output_path)
            self.event_logger.log(
                "pdf_document_generated",
                message="PDF gerado",
                template_path=str(self.template_path),
                template_hash=self.template_semantic_hash,
                output_path=str(output_path),
                report=summary,
            )
            try:
                self._save_autosave_snapshot()
            except Exception as exc:
                self.event_logger.log(
                    "autosave_save_error",
                    level="warning",
                    message="Falha ao salvar autosave PDF",
                    template_path=str(self.template_path),
                    output_path=str(output_path),
                    error=str(exc),
                )
            self.refresh_session_views()
            self._set_status("PDF gerado")
        except Exception as exc:
            self.event_logger.log(
                "pdf_generation_error",
                level="error",
                message="Falha ao gerar PDF",
                template_path=str(self.template_path),
                output_path=str(output_path),
                error=str(exc),
            )
            messagebox.showerror("Erro ao gerar", f"Nao foi possivel gerar o PDF:\n{exc}")

    def rewrite_template_with_markers(self) -> None:
        if not self.template_path:
            messagebox.showerror("Erro", "Selecione um template .docx ou .pdf antes de reescrever marcadores.")
            return
        if self._is_pdf_template():
            self._rewrite_pdf_with_markers()
            return

        reader = self._get_reader()
        if reader is None:
            messagebox.showerror("Erro", "Nao foi possivel ler o template atual.")
            return

        output_folder = Path(self.output_folder or self.template_path.parent)
        try:
            output_folder.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            messagebox.showerror("Pasta de saida invalida", f"Nao foi possivel criar a pasta de saida:\n{exc}")
            return

        output_path = self._next_available_path(output_folder / f"TEMPLATE_MARCADO - {self.template_path.name}")
        try:
            extraction = extract_fields(reader.extract_text({}))
            report = rewrite_template_with_markers(self.template_path, output_path, extraction)
            summary = report.to_dict()
            lines = [
                f"Template marcado gerado em:\n{output_path}",
                "",
                f"Campos marcados: {len(summary['marked_fields'])}",
                f"Campos em revisao: {len(summary['review_fields'])}",
                f"Campos ignorados: {len(summary['ignored_fields'])}",
            ]
            if summary["ignored_fields"]:
                lines.append("")
                lines.append("Ignorados:")
                lines.extend(f"- {item}" for item in summary["ignored_fields"][:6])
            messagebox.showinfo("Template marcado", "\n".join(lines))
            self.event_logger.log(
                "template_rewritten_with_markers",
                message="Template reescrito com marcadores",
                template_path=str(self.template_path),
                output_path=str(output_path),
                report=summary,
            )
            self._set_status("Template marcado gerado")
        except Exception as exc:
            self.event_logger.log(
                "template_rewrite_error",
                level="error",
                message="Falha ao reescrever template com marcadores",
                template_path=str(self.template_path),
                output_path=str(output_path),
                error=str(exc),
            )
            messagebox.showerror("Erro ao reescrever", f"Nao foi possivel gerar o template marcado:\n{exc}")

    def _rewrite_pdf_with_markers(self) -> None:
        handler = self._get_pdf_handler()
        if handler is None or self.template_path is None:
            messagebox.showerror("Erro", "Nao foi possivel ler o PDF atual.")
            return

        output_folder = Path(self.output_folder or self.template_path.parent)
        try:
            output_folder.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            messagebox.showerror("Pasta de saida invalida", f"Nao foi possivel criar a pasta de saida:\n{exc}")
            return

        output_path = self._next_available_path(output_folder / f"TEMPLATE_MARCADO - {self.template_path.name}")
        try:
            report = handler.generate_marked_pdf(
                output_path,
                manual_areas=self.pdf_area_mappings,
                detections=self.template_semantic_detections,
            )
            summary = report.to_dict()
            lines = [
                f"PDF marcado gerado em:\n{output_path}",
                "",
                f"Areas manuais marcadas: {len(summary['manual_fields'])}",
                f"Campos detectados marcados: {len(summary['auto_fields'])}",
                f"Itens ignorados: {len(summary['skipped'])}",
            ]
            if summary["skipped"]:
                lines.append("")
                lines.append("Ignorados:")
                lines.extend(f"- {item}" for item in summary["skipped"][:6])
            messagebox.showinfo("PDF marcado", "\n".join(lines))
            self.event_logger.log(
                "pdf_template_rewritten_with_markers",
                message="PDF reescrito com marcadores",
                template_path=str(self.template_path),
                output_path=str(output_path),
                report=summary,
            )
            self._set_status("PDF marcado gerado")
        except Exception as exc:
            self.event_logger.log(
                "pdf_template_rewrite_error",
                level="error",
                message="Falha ao reescrever PDF com marcadores",
                template_path=str(self.template_path),
                output_path=str(output_path),
                error=str(exc),
            )
            messagebox.showerror("Erro ao reescrever", f"Nao foi possivel gerar o PDF marcado:\n{exc}")

    def save_mapping(self) -> None:
        if self.custom_marker is None or self.custom_value is None:
            return
        marker = self.custom_marker.get().strip()
        value = self.custom_value.get().strip()

        try:
            normalized_marker = self.mapping_manager.normalize_marker(marker)
            self.mapping_manager.add_marker(marker, value)
            self.custom_marker.delete(0, "end")
            self.custom_value.delete(0, "end")
            self.refresh_mapping_view()
            self.update_preview()
            messagebox.showinfo("Mapeamento", f"Marcador {normalized_marker} salvo com sucesso.")
        except ValueError as exc:
            messagebox.showerror("Erro", str(exc))

    def refresh_mapping_view(self) -> None:
        if self.mapping_view is None:
            return
        data = self.mapping_manager.load()
        lines = ["Nenhum marcador adicional cadastrado."] if not data else [f"{key} = {value}" for key, value in sorted(data.items())]
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
        if not self.template_semantic_hash or not self.template_path:
            self._set_textbox(self.profile_summary_view, t("settings_profile_empty"))
            return

        summary = self.profile_store.summarize(self.template_semantic_hash)
        learned_fields = summary.get("learned_fields", [])
        corrections = summary.get("corrections", [])
        history = summary.get("history", [])
        lines = [
            f"{t('settings_profile_template')}: {summary.get('template_name') or self.template_path.name}",
            f"{t('settings_profile_hash')}: {summary.get('hash', self.template_semantic_hash)[:12]}...",
            f"{t('settings_profile_usage')}: {summary.get('usage_count', 0)}",
            f"{t('settings_profile_fields')}: {len(learned_fields)}",
            f"{t('settings_profile_corrections')}: {len(corrections)}",
        ]
        if learned_fields:
            labels = [FIELD_LABELS.get(field, field) for field in learned_fields[:6]]
            lines.append(f"{t('settings_profile_learned')}: {', '.join(labels)}")
        if history:
            lines.append(f"{t('settings_profile_last_event')}: {history[-1].get('event', '-')}")
        self._set_textbox(self.profile_summary_view, "\n".join(lines))

    def refresh_session_views(self) -> None:
        if self.session_history_view is None and self.session_status_label is None and self.restore_session_button is None:
            return

        settings = self.session_store.load()
        recent_templates = self.session_store.recent_templates()
        recent_documents = self.session_store.recent_documents()
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
            log_path = self.event_logger.base_dir
            text = f"{t('settings_logs_path')}: {log_path}"
            if autosave and autosave.get("template_path"):
                text += f"\n{t('settings_autosave_path')}: {autosave.get('template_path')}"
            last_output = settings.get("last_output_folder", "")
            if last_output:
                text += f"\n{t('settings_last_folder')}: {last_output}"
            self.session_status_label.configure(text=text)

        if self.restore_session_button is not None:
            self.restore_session_button.configure(state="normal" if autosave else "disabled")

    def _record_template_profile(self) -> None:
        if not self.template_path or not self.template_semantic_hash:
            return
        self.profile_store.update_profile(
            self.template_semantic_hash,
            self.template_path.name,
            detections=self.template_semantic_detections,
            placeholders=sorted(self.template_placeholders),
            required_fields=set(self.form_panel.REQUIRED_MARKERS),
            manual_values=self.form_panel.get_values(),
        )

    def _record_template_usage(self) -> None:
        if not self.template_path or not self.template_semantic_hash:
            return
        self.session_store.set_last_template(
            self.template_path,
            self.template_path.name,
            self.template_semantic_hash,
            self.form_panel.get_values(),
        )

    def _schedule_autosave_snapshot(self) -> None:
        if self._autosave_job is not None:
            try:
                self.after_cancel(self._autosave_job)
            except Exception:
                pass
        self._autosave_job = self.after(2000, self._run_autosave_snapshot)

    def _run_autosave_snapshot(self) -> None:
        self._autosave_job = None
        try:
            self._save_autosave_snapshot()
        except Exception as exc:
            self.event_logger.log(
                "autosave_save_error",
                level="warning",
                message="Falha ao salvar autosave",
                template_path=str(self.template_path) if self.template_path else "",
                error=str(exc),
            )

    def _save_autosave_snapshot(self) -> None:
        if self._state_sync_suspended:
            return
        if self.template_path is None:
            return
        values = self.form_panel.get_values()
        detected_fields = {
            marker: detection.to_dict()
            for marker, detection in self.template_semantic_detections.items()
            if detection.value
        }
        pdf_area_data = {
            marker: [area.to_dict() for area in areas]
            for marker, areas in self.pdf_area_mappings.items()
        }
        self.session_store.save_autosave(
            self.template_path,
            self.template_path.name,
            self.template_semantic_hash,
            self.output_folder,
            values,
            current_view="main",
            detected_fields=detected_fields,
            pdf_area_mappings=pdf_area_data,
        )
        self.session_store.set_last_template(
            self.template_path,
            self.template_path.name,
            self.template_semantic_hash or "",
            values,
        )
        self.event_logger.log(
            "autosave_saved",
            message="Estado salvo automaticamente",
            template_path=str(self.template_path),
            template_hash=self.template_semantic_hash,
            output_folder=str(self.output_folder) if self.output_folder else "",
        )

    def _maybe_restore_saved_session_on_startup(self) -> None:
        autosave = self.session_store.load_autosave()
        if not autosave:
            self.update_preview()
            return
        if os.environ.get("PYTEST_CURRENT_TEST"):
            self.update_preview()
            return
        if messagebox.askyesno(t("history_title"), t("restore_session_prompt")):
            if not self._restore_saved_session():
                self.update_preview()
            return
        self.update_preview()

    def restore_saved_session(self) -> None:
        if not self._restore_saved_session():
            messagebox.showinfo(t("settings_session_title"), t("settings_restore_empty"))

    def _restore_saved_session(self) -> bool:
        autosave = self.session_store.load_autosave()
        if not autosave:
            return False
        template_path_text = str(autosave.get("template_path", "")).strip()
        if not template_path_text:
            return False
        template_path = Path(template_path_text)
        if not template_path.exists():
            self.event_logger.log(
                "autosave_restore_failed",
                level="error",
                message="Template salvo no autosave não foi encontrado",
                template_path=template_path_text,
            )
            return False

        self.load_template(template_path, show_errors=False)
        values = autosave.get("values", {})
        if isinstance(values, dict):
            self.form_panel.set_values({str(key): str(value) for key, value in values.items()}, only_empty=False)
        pdf_area_data = autosave.get("pdf_area_mappings", {})
        if isinstance(pdf_area_data, dict):
            restored_areas: dict[str, list[PDFManualArea]] = {}
            for marker, areas in pdf_area_data.items():
                if not isinstance(areas, list):
                    continue
                restored_areas[str(marker)] = [
                    PDFManualArea.from_dict({"marker": str(marker), **area})
                    for area in areas
                    if isinstance(area, dict)
                ]
            self.pdf_area_mappings = {marker: areas for marker, areas in restored_areas.items() if areas}
        output_folder = autosave.get("output_folder", "")
        if output_folder:
            self.output_folder = Path(str(output_folder))
            self._refresh_status_context()
        self._schedule_autosave_snapshot()
        self.update_preview()
        self.refresh_session_views()
        self.event_logger.log(
            "autosave_restored",
            message="Sessão restaurada",
            template_path=str(template_path),
            template_hash=autosave.get("template_hash", ""),
        )
        self._set_status("Sessão restaurada")
        return True

    def refresh_template_mapping_view(self) -> None:
        if self.semantic_rows_frame is None:
            return
        for child in self.semantic_rows_frame.winfo_children():
            child.destroy()

        if self.semantic_warning_label is not None:
            self.semantic_warning_label.destroy()
            self.semantic_warning_label = None

        self._refresh_template_profile_summary()

        if not self.template_path or not self.template_semantic_hash:
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
            detection = self.template_semantic_detections.get(marker)
            value = detection.value if detection and detection.value else "-"
            source = self._semantic_source_text(detection)
            confidence = f"{int(round(detection.confidence * 100))}%" if detection and detection.value else "-"

            ctk.CTkLabel(
                self.semantic_rows_frame,
                text=label,
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
                command=lambda _marker=marker: self.accept_template_detection(_marker),
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
                command=lambda _marker=marker: self.correct_template_detection(_marker),
            ).grid(row=0, column=1, sticky="ew")

        if self.semantic_generation_warnings:
            self.semantic_warning_label = ctk.CTkLabel(
                self.semantic_rows_frame,
                text="\n".join(self.semantic_generation_warnings[:3]),
                text_color=COLORS["red"],
                font=font(10, "bold"),
                anchor="w",
                justify="left",
                wraplength=760,
            )
            self.semantic_warning_label.grid(row=len(FIELD_LABELS) + 1, column=0, columnspan=5, sticky="ew", padx=10, pady=(10, 10))

    def accept_template_detection(self, marker: str) -> None:
        if not self.template_semantic_hash:
            return
        detection = self.template_semantic_detections.get(marker)
        if not detection or not detection.value:
            messagebox.showinfo(t("template_mapping_title"), t("template_mapping_no_value"))
            return
        self.form_panel.set_field_value(marker, detection.value, detected=True)
        self.semantic_analyzer.accept_detection(self.template_semantic_hash, detection)
        self.profile_store.record_correction(self.template_semantic_hash, self.template_path.name if self.template_path else "", detection, action="accepted_detection")
        self.event_logger.log(
            "template_detection_accepted",
            message="Detecção aceita",
            template_hash=self.template_semantic_hash,
            field=marker,
            value=detection.value,
            confidence=detection.confidence,
        )
        self._schedule_autosave_snapshot()
        self.refresh_template_mapping_view()
        self.refresh_session_views()
        self.update_preview()
        self._set_status("Mapeamento aceito")

    def correct_template_detection(self, marker: str) -> None:
        if not self.template_semantic_hash:
            return
        value = self.form_panel.get_values().get(marker, "").strip()
        if not value:
            messagebox.showinfo(t("template_mapping_title"), "Preencha o campo na lateral antes de corrigir o mapeamento.")
            return
        detection = self.semantic_analyzer.save_manual_value(self.template_semantic_hash, marker, value)
        self.template_semantic_detections[marker] = detection
        self.profile_store.record_correction(self.template_semantic_hash, self.template_path.name if self.template_path else "", detection, action="manual_correction")
        self.event_logger.log(
            "template_detection_corrected",
            message="Detecção corrigida manualmente",
            template_hash=self.template_semantic_hash,
            field=marker,
            value=value,
        )
        self.form_panel.clear_detected_indicator(marker)
        self._schedule_autosave_snapshot()
        self.refresh_template_mapping_view()
        self.refresh_session_views()
        self.update_preview()
        self._set_status("Mapeamento corrigido")

    def _reset_template_semantics(self) -> None:
        self.template_semantic_hash = None
        self.template_placeholders = set()
        self.template_semantic_auto_detections = {}
        self.template_semantic_detections = {}
        self.semantic_generation_warnings = []
        self.last_safe_semantic_result = None
        self.pdf_area_mappings = {}
        self._visible_history_suggestions.clear()
        self._last_history_suggestion_signature = None
        self.form_panel.clear_history_suggestions()
        self.refresh_template_mapping_view()

    def load_template(self, file_path: str | Path, show_errors: bool = True) -> None:
        path = Path(file_path)
        if not path.exists():
            self.template_path = None
            self.reader = None
            self.pdf_handler = None
            self.template_kind = "docx"
            self._reset_template_semantics()
            message = f"Template não encontrado:\n{path}"
            self._set_status("Template não encontrado")
            if show_errors:
                messagebox.showerror("Erro", message)
            else:
                self.preview_panel.set_text(message)
            return

        validation_error = self._validate_template_path(path)
        if validation_error:
            self.template_path = None
            self.reader = None
            self.pdf_handler = None
            self.template_kind = "docx"
            self.template_placeholders = set()
            self.template_suggestions = {}
            self._reset_template_semantics()
            self.preview_panel.set_text(validation_error)
            self.preview_panel.set_model_name("Nenhum modelo")
            self.preview_panel.set_marker_count(0)
            self._refresh_status_context()
            self._set_status("Arquivo não suportado")
            if show_errors:
                messagebox.showerror("Arquivo Word não suportado", validation_error)
            return

        if path.suffix.lower() == ".pdf":
            self._load_pdf_template(path, show_errors=show_errors)
            return

        self.template_path = path
        self.reader = DOCXReader(path)
        self.pdf_handler = None
        self.template_kind = "docx"
        self.pdf_area_mappings = {}
        try:
            self._state_sync_suspended = True
            self.preview_panel.set_loading(t("loading_template"))
            self.update_idletasks()
            analysis = self.reader.analyze_template()
            self.template_placeholders = {
                marker
                for marker in analysis.get("placeholders", [])
                if isinstance(marker, str) and marker.startswith("{{") and marker.endswith("}}")
            }
            self.template_semantic_hash = self.semantic_analyzer.template_hash(path)
            self.template_semantic_detections = self.semantic_analyzer.analyze(path)
            saved_profile = self.semantic_analyzer.load_template_mapping(self.template_semantic_hash)
            auto_saved = saved_profile.get("auto_detections", {}) if isinstance(saved_profile, dict) else {}
            self.template_semantic_auto_detections = {
                field: SemanticDetection.from_dict(data)
                for field, data in auto_saved.items()
                if isinstance(data, dict)
            }
            if not self.template_semantic_auto_detections:
                self.template_semantic_auto_detections = dict(self.template_semantic_detections)
            self.semantic_generation_warnings = []
            semantic_suggestions = self.semantic_analyzer.suggestion_values(self.template_semantic_detections)
            legacy_suggestions = self.reader.suggest_values()
            self.template_suggestions = dict(semantic_suggestions)
            for marker, value in legacy_suggestions.items():
                self.template_suggestions.setdefault(marker, value)

            detected = self.form_panel.set_detected_values(self.template_semantic_detections, only_empty=True)
            legacy_only = {
                marker: value
                for marker, value in legacy_suggestions.items()
                if marker not in semantic_suggestions
            }
            detected += self.form_panel.set_values(legacy_only, only_empty=True)
            self.update_preview()
            self.analyze_template_section()
            self.refresh_template_mapping_view()
            self._state_sync_suspended = False
            self._record_template_profile()
            self._record_template_usage()
            self._schedule_autosave_snapshot()
            self._schedule_history_suggestions_update()
            self.refresh_session_views()
            self.event_logger.log(
                "template_loaded",
                message="Template carregado",
                template_path=str(self.template_path),
                template_hash=self.template_semantic_hash,
                placeholders=len(self.template_placeholders),
                detected_fields=len(self.template_suggestions),
            )

            if analysis["placeholders"]:
                self._set_status(f"{len(analysis['placeholders'])} marcadores")
            elif self.template_suggestions:
                self._set_status(f"{detected} campos detectados")
            else:
                self._set_status("Template carregado")
        except Exception as exc:
            self.template_path = None
            self.reader = None
            self.template_suggestions = {}
            self._reset_template_semantics()
            self._refresh_status_context()
            self.preview_panel.set_text(f"Não foi possível carregar o template:\n{exc}")
            self.preview_panel.set_model_name("Template inválido")
            self.preview_panel.set_marker_count(0)
            self._set_status("Erro ao carregar")
            self.event_logger.log(
                "template_load_error",
                level="error",
                message="Falha ao carregar template",
                template_path=str(path),
                error=str(exc),
            )
            if show_errors:
                messagebox.showerror("Erro ao carregar", f"Não foi possível carregar o template:\n{exc}")
        finally:
            self._state_sync_suspended = False

    def _load_pdf_template(self, path: Path, show_errors: bool = True) -> None:
        self.template_path = path
        self.reader = None
        self.pdf_handler = PDFHandler(path)
        self.template_kind = "pdf"
        self.pdf_area_mappings = {}
        try:
            self._state_sync_suspended = True
            self.preview_panel.set_loading(t("loading_template"))
            self.update_idletasks()
            analysis = self.pdf_handler.analyze_template()
            self.template_placeholders = {
                marker
                for marker in analysis.get("placeholders", [])
                if isinstance(marker, str) and marker.startswith("{{") and marker.endswith("}}")
            }
            self.template_semantic_hash = PDFHandler.template_hash(path)
            auto_detections = self.pdf_handler.detect_fields()
            saved_profile = self.semantic_analyzer.load_template_mapping(self.template_semantic_hash)
            accepted = saved_profile.get("accepted", {}) if isinstance(saved_profile, dict) else {}
            self.template_semantic_detections = dict(auto_detections)
            for field, data in accepted.items():
                if field in FIELD_LABELS and isinstance(data, dict):
                    detection = SemanticDetection.from_dict(data)
                    if detection.value:
                        self.template_semantic_detections[field] = detection
            self.template_semantic_auto_detections = dict(auto_detections)
            self.semantic_analyzer.save_detections(
                self.template_semantic_hash,
                path.name,
                auto_detections,
                self.template_semantic_detections,
            )
            self.semantic_generation_warnings = []
            semantic_suggestions = self.semantic_analyzer.suggestion_values(self.template_semantic_detections)
            legacy_suggestions = self.pdf_handler.suggest_values()
            self.template_suggestions = dict(semantic_suggestions)
            for marker, value in legacy_suggestions.items():
                self.template_suggestions.setdefault(marker, value)

            detected = self.form_panel.set_detected_values(self.template_semantic_detections, only_empty=True)
            legacy_only = {
                marker: value
                for marker, value in legacy_suggestions.items()
                if marker not in semantic_suggestions
            }
            detected += self.form_panel.set_values(legacy_only, only_empty=True)
            self.update_preview()
            self.analyze_template_section()
            self.refresh_template_mapping_view()
            self._state_sync_suspended = False
            self._record_template_profile()
            self._record_template_usage()
            self._schedule_autosave_snapshot()
            self._schedule_history_suggestions_update()
            self.refresh_session_views()
            self.event_logger.log(
                "pdf_template_loaded",
                message="PDF carregado",
                template_path=str(self.template_path),
                template_hash=self.template_semantic_hash,
                placeholders=len(self.template_placeholders),
                detected_fields=len(self.template_suggestions),
                pages=analysis.get("pages", 0),
                text_blocks=analysis.get("text_blocks", 0),
            )
            if self.template_suggestions:
                self._set_status(f"PDF carregado: {detected} campos detectados")
            else:
                self._set_status("PDF carregado")
        except Exception as exc:
            self.template_path = None
            self.reader = None
            self.pdf_handler = None
            self.template_kind = "docx"
            self.template_suggestions = {}
            self._reset_template_semantics()
            self._refresh_status_context()
            self.preview_panel.set_text(f"Nao foi possivel carregar o PDF:\n{exc}")
            self.preview_panel.set_model_name("PDF invalido")
            self.preview_panel.set_marker_count(0)
            self._set_status("Erro ao carregar PDF")
            self.event_logger.log(
                "pdf_template_load_error",
                level="error",
                message="Falha ao carregar PDF",
                template_path=str(path),
                error=str(exc),
            )
            if show_errors:
                messagebox.showerror("Erro ao carregar", f"Nao foi possivel carregar o PDF:\n{exc}")
        finally:
            self._state_sync_suspended = False

    def request_preview_update(self) -> None:
        if self._state_sync_suspended:
            return
        if self._preview_job is not None:
            self.after_cancel(self._preview_job)
        self._preview_job = self.after(250, self._run_scheduled_preview)
        self._schedule_autosave_snapshot()
        self._schedule_history_suggestions_update()

    def _run_scheduled_preview(self) -> None:
        self._preview_job = None
        self.update_preview()

    def _schedule_history_suggestions_update(self) -> None:
        if self._suggestion_job is not None:
            try:
                self.after_cancel(self._suggestion_job)
            except Exception:
                pass
        self._suggestion_job = self.after(250, self._run_history_suggestions_update)

    def _run_history_suggestions_update(self) -> None:
        self._suggestion_job = None
        self._refresh_history_suggestions()

    def _refresh_history_suggestions(self) -> None:
        if self.template_path is None:
            self.form_panel.clear_history_suggestions()
            self._visible_history_suggestions.clear()
            self._last_history_suggestion_signature = None
            return

        current_values = self.form_panel.get_values()
        signature = (
            self.template_semantic_hash or "",
            current_values.get("{{COMPRADOR}}", "").strip(),
            current_values.get("{{VENDEDOR}}", "").strip(),
            tuple(sorted(self._ignored_history_suggestions)),
        )
        if signature == self._last_history_suggestion_signature:
            return
        suggestions = self.history_suggestions.build_suggestions(
            current_values,
            template_hash=self.template_semantic_hash or "",
            ignored_keys=self._ignored_history_suggestions,
        )
        self._visible_history_suggestions = suggestions
        self._last_history_suggestion_signature = signature
        visible_markers = set(suggestions)
        for marker, suggestion in suggestions.items():
            self.form_panel.set_history_suggestion(
                marker,
                suggestion,
                apply_command=lambda _marker=marker: self.apply_history_suggestion(_marker),
                ignore_command=lambda _marker=marker: self.ignore_history_suggestion(_marker),
            )
        for marker in list(self.form_panel.suggestion_frames):
            if marker not in visible_markers:
                self.form_panel.clear_history_suggestion(marker)

    def _get_reader(self) -> DOCXReader | None:
        if self.template_path is None or self.template_kind == "pdf":
            return None
        if self.reader is None:
            self.reader = DOCXReader(self.template_path)
        return self.reader

    def _get_pdf_handler(self) -> PDFHandler | None:
        if self.template_path is None or self.template_kind != "pdf":
            return None
        if self.pdf_handler is None:
            self.pdf_handler = PDFHandler(self.template_path)
        return self.pdf_handler

    def _is_pdf_template(self) -> bool:
        return self.template_kind == "pdf"

    def _flatten_pdf_areas(self) -> list[PDFManualArea]:
        areas: list[PDFManualArea] = []
        for marker_areas in self.pdf_area_mappings.values():
            areas.extend(marker_areas)
        return areas

    def _build_replacements(self) -> dict[str, str]:
        values = self.form_panel.get_values()
        replacements = self.mapping_manager.build_replacements(values)
        reader = self._get_reader()
        if reader is not None:
            document_text = reader.extract_text({})
            semantic_sources = self._build_semantic_source_map()
            placeholder_replacements = {
                marker: values.get(marker, "")
                for marker in self.template_placeholders
                if marker in values
            }
            safe_result = build_safe_semantic_replacements(
                semantic_sources,
                values,
                placeholder_replacements,
                document_text,
            )
            self.last_safe_semantic_result = safe_result
            replacements.update(safe_result.safe_replacements)
            self.semantic_generation_warnings = safe_result.warnings
        else:
            self.last_safe_semantic_result = None
            self.semantic_generation_warnings = []
        return replacements

    def _build_semantic_source_map(self) -> dict[str, SemanticDetection]:
        semantic_sources: dict[str, SemanticDetection] = dict(self.template_semantic_auto_detections or self.template_semantic_detections)
        reader = self._get_reader()
        if reader is not None:
            for marker, value in reader.suggest_values().items():
                if marker in semantic_sources:
                    continue
                semantic_sources[marker] = SemanticDetection(
                    field=marker,
                    value=value,
                    confidence=0.92,
                    source="legacy: reader.suggest_values",
                    snippet=value,
                )
        return semantic_sources

    def _set_status(self, text: str) -> None:
        self.status_label.configure(text=text)
        self.footer_status_label.configure(text=text)

    def _refresh_status_context(self) -> None:
        template = self.template_path.name if self.template_path else "nenhum"
        output = self.output_folder.name if self.output_folder else "não definida"
        if len(template) > 44:
            template = f"...{template[-41:]}"
        if len(output) > 38:
            output = f"...{output[-35:]}"
        self.template_status_label.configure(text=template)
        self.output_status_label.configure(text=output)

    def _pulse_dot(self) -> None:
        self._pulse_state = not self._pulse_state
        color = COLORS["green4"] if self._pulse_state else COLORS["green2"]
        self.status_dot.configure(text_color=color)
        self.footer_status_dot.configure(text_color=color)
        self._pulse_job = self.after(900, self._pulse_dot)

    @staticmethod
    def _separator(parent, column: int) -> None:
        ctk.CTkFrame(parent, fg_color=COLORS["border"], width=1, corner_radius=0).grid(row=0, column=column, sticky="ns", padx=(12, 0), pady=7)

    @staticmethod
    def _validate_template_path(path: Path) -> str | None:
        if path.name.startswith("~$"):
            return (
                "Esse é um arquivo temporário do Word.\n\n"
                "Feche o documento no Word e selecione o arquivo original .docx."
            )
        if path.suffix.lower() == ".doc":
            return (
                "Arquivos .doc antigos não são suportados diretamente.\n\n"
                "Abra no Microsoft Word e salve como .docx, depois adicione o novo arquivo."
            )
        if path.suffix.lower() == ".pdf":
            if not pdf_support_available():
                return "Suporte a PDF indisponivel. Instale PyMuPDF para abrir arquivos .pdf."
            return None
        if path.suffix.lower() != ".docx":
            return "Selecione um arquivo Word no formato .docx ou um PDF no formato .pdf."
        return None

    def close_app(self) -> None:
        try:
            self._save_autosave_snapshot()
        except Exception as exc:
            self.event_logger.log(
                "autosave_save_error",
                level="warning",
                message="Falha ao salvar autosave ao encerrar",
                template_path=str(self.template_path) if self.template_path else "",
                error=str(exc),
            )
        self.event_logger.log(
            "application_closed",
            message="Aplicação encerrada",
            template_path=str(self.template_path) if self.template_path else "",
            template_hash=self.template_semantic_hash,
            output_folder=str(self.output_folder) if self.output_folder else "",
        )
        if self._preview_job is not None:
            try:
                self.after_cancel(self._preview_job)
            except Exception:
                pass
            self._preview_job = None
        if self._suggestion_job is not None:
            try:
                self.after_cancel(self._suggestion_job)
            except Exception:
                pass
            self._suggestion_job = None
        if self._pulse_job is not None:
            try:
                self.after_cancel(self._pulse_job)
            except Exception:
                pass
            self._pulse_job = None
        if self._splash_job is not None:
            try:
                self.after_cancel(self._splash_job)
            except Exception:
                pass
            self._splash_job = None
        if self._autosave_job is not None:
            try:
                self.after_cancel(self._autosave_job)
            except Exception:
                pass
            self._autosave_job = None
        if self.splash_frame is not None:
            self.splash_frame.destroy()
            self.splash_frame = None
        self.destroy()

    def _apply_window_icon(self) -> None:
        try:
            icon_path = self._asset_path("app_icon.ico")
            if icon_path.exists():
                self.iconbitmap(str(icon_path))
        except Exception:
            pass

    @staticmethod
    def _asset_path(name: str) -> Path:
        base = getattr(sys, "_MEIPASS", None)
        if base:
            return Path(base) / "assets" / name
        return Path(__file__).resolve().parent.parent / "assets" / name

    @staticmethod
    def _sanitize_filename(value: str) -> str:
        invalid_chars = '<>:"/\\|?*'
        sanitized = "".join(
            "_" if ch in invalid_chars or ord(ch) < 32 else ch
            for ch in value.upper()
            if ch.isalnum() or ch in (" ", "_", "-") or ch in invalid_chars
        )
        sanitized = "_".join(sanitized.split())
        sanitized = sanitized.strip(" ._")
        return sanitized[:90].rstrip(" .") or "DOCUMENTO"

    @staticmethod
    def _next_available_path(path: Path) -> Path:
        if not path.exists():
            return path

        for index in range(2, 1000):
            candidate = path.with_name(f"{path.stem} ({index}){path.suffix}")
            if not candidate.exists():
                return candidate
        raise FileExistsError("Não foi possível encontrar um nome livre para o arquivo gerado.")

    @staticmethod
    def _set_textbox(textbox, value: str) -> None:
        textbox.configure(state="normal")
        textbox.delete("1.0", "end")
        textbox.insert("1.0", value)
        textbox.configure(state="disabled")
