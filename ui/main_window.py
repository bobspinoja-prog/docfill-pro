import sys
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image

from services.docx_reader import DOCXReader
from services.docx_writer import DOCXWriter
from services.mapping_manager import MappingManager
from ui.form_panel import FormPanel
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
        self.template_suggestions: dict[str, str] = {}
        self._preview_job: str | None = None
        self._pulse_job: str | None = None
        self._splash_job: str | None = None
        self._pulse_state = False
        self.mapping_manager = MappingManager()
        self.logo_image = None
        self.splash_symbol_image = None
        self.splash_frame = None
        self.mapping_window = None
        self.about_window = None
        self.analysis_view = None
        self.mapping_view = None
        self.custom_marker = None
        self.custom_value = None
        self.about_symbol_image = None

        self._build_ui()
        self._show_startup_splash()
        self._pulse_dot()
        if initial_template:
            self.load_template(initial_template, show_errors=False)
        else:
            self.update_preview()
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

        self.preview_panel = PreviewPanel(body, on_refresh=self.update_preview)
        self.preview_panel.grid(row=0, column=0, sticky="nsew")

        ctk.CTkFrame(body, fg_color=COLORS["border"], width=1, corner_radius=0).grid(row=0, column=1, sticky="ns")

        self.form_panel = FormPanel(
            body,
            on_update=self.request_preview_update,
            callbacks={
                "select_template": self.select_template,
                "select_output": self.select_output,
                "generate": self.generate_document,
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
            text=t("app_name") + " v1.1.0",
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
            self.analyze_template_section()
            return

        window = ctk.CTkToplevel(self)
        window.title(t("settings_title"))
        window.geometry("900x700")
        window.minsize(760, 560)
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
        wrapper.grid_rowconfigure(2, weight=1)

        analysis_card = ctk.CTkFrame(wrapper, fg_color=COLORS["bg3"], corner_radius=8, border_width=1, border_color=COLORS["border2"])
        analysis_card.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 10))
        analysis_card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(analysis_card, text=t("settings_analysis"), font=font(14, "bold"), text_color=COLORS["green3"], anchor="w").grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 6))
        ctk.CTkButton(analysis_card, text=t("settings_analyze_button"), fg_color=COLORS["green"], hover_color=COLORS["green2"], command=self.analyze_template_section).grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 8))
        self.analysis_view = ctk.CTkTextbox(analysis_card, fg_color=COLORS["input"], text_color=COLORS["text"], border_width=1, border_color=COLORS["border3"], font=font(12), height=150)
        self.analysis_view.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 14))
        self.analysis_view.configure(state="disabled")

        form_card = ctk.CTkFrame(wrapper, fg_color=COLORS["bg3"], corner_radius=8, border_width=1, border_color=COLORS["border2"])
        form_card.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 10))
        form_card.grid_columnconfigure(0, weight=1)
        form_card.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(form_card, text=t("settings_add_marker"), font=font(14, "bold"), text_color=COLORS["green3"], anchor="w").grid(row=0, column=0, columnspan=2, sticky="ew", padx=14, pady=(12, 6))
        self.custom_marker = ctk.CTkEntry(form_card, placeholder_text="Ex.: TELEFONE", fg_color=COLORS["input"], border_color=COLORS["border3"], text_color=COLORS["text"])
        self.custom_marker.grid(row=1, column=0, sticky="ew", padx=(14, 6), pady=(0, 12))
        self.custom_value = ctk.CTkEntry(form_card, placeholder_text="Valor do marcador", fg_color=COLORS["input"], border_color=COLORS["border3"], text_color=COLORS["text"])
        self.custom_value.grid(row=1, column=1, sticky="ew", padx=(6, 14), pady=(0, 12))
        ctk.CTkButton(form_card, text=t("settings_save_marker"), fg_color=COLORS["green"], hover_color=COLORS["green2"], command=self.save_mapping).grid(row=2, column=0, columnspan=2, sticky="ew", padx=14, pady=(0, 14))

        list_card = ctk.CTkFrame(wrapper, fg_color=COLORS["bg3"], corner_radius=8, border_width=1, border_color=COLORS["border2"])
        list_card.grid(row=2, column=0, sticky="nsew", padx=14, pady=(0, 14))
        list_card.grid_columnconfigure(0, weight=1)
        list_card.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(list_card, text=t("settings_list_title"), font=font(14, "bold"), text_color=COLORS["green3"], anchor="w").grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 6))
        self.mapping_view = ctk.CTkTextbox(list_card, fg_color=COLORS["input"], text_color=COLORS["text"], border_width=1, border_color=COLORS["border3"], font=font(12))
        self.mapping_view.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
        self.mapping_view.configure(state="disabled")

        self.refresh_mapping_view()
        self.analyze_template_section()

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

    def analyze_template_section(self) -> None:
        if self.analysis_view is None:
            return
        if not self.template_path:
            self._set_textbox(self.analysis_view, "Selecione um template .docx para iniciar a análise.")
            return

        try:
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
            title="Selecionar Template DOCX",
            filetypes=[
                ("Word moderno (.docx)", "*.docx"),
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
            self._refresh_status_context()
            self._set_status("Pasta definida")

    def clear_form(self) -> None:
        self.form_panel.clear()
        self._set_status("Campos limpos")

    def generate_document(self) -> None:
        if not self.template_path:
            messagebox.showerror("Erro", "Selecione um template .docx antes de gerar o documento.")
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

        replacements = self._build_replacements()
        comprador = values.get("{{COMPRADOR}}", "").strip()
        sanitized_name = self._sanitize_filename(comprador)
        output_path = self._next_available_path(Path(output_folder) / f"DECLARACAO - {sanitized_name}.docx")

        try:
            writer = DOCXWriter()
            writer.generate(self.template_path, output_path, replacements)
            messagebox.showinfo("Sucesso", f"Documento gerado com sucesso em:\n{output_path}")
            self._set_status("Documento gerado")
        except Exception as exc:
            messagebox.showerror("Erro ao gerar", f"Não foi possível gerar o arquivo: {exc}")

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

    def load_template(self, file_path: str | Path, show_errors: bool = True) -> None:
        path = Path(file_path)
        if not path.exists():
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
            self.template_suggestions = {}
            self.preview_panel.set_text(validation_error)
            self.preview_panel.set_model_name("Nenhum modelo")
            self.preview_panel.set_marker_count(0)
            self._refresh_status_context()
            self._set_status("Arquivo não suportado")
            if show_errors:
                messagebox.showerror("Arquivo Word não suportado", validation_error)
            return

        self.template_path = path
        self.reader = DOCXReader(path)
        try:
            self.preview_panel.set_loading(t("loading_template"))
            self.update_idletasks()
            analysis = self.reader.analyze_template()
            self.template_suggestions = self.reader.suggest_values()
            detected = self.form_panel.set_values(self.template_suggestions, only_empty=True)
            self.update_preview()
            self.analyze_template_section()

            if analysis["placeholders"]:
                self._set_status(f"{len(analysis['placeholders'])} marcadores")
            elif self.template_suggestions:
                self._set_status(f"{detected} campos detectados")
            else:
                self._set_status("Template carregado")
        except Exception as exc:
            self.template_suggestions = {}
            self.preview_panel.set_text(f"Não foi possível carregar o template:\n{exc}")
            self.preview_panel.set_model_name("Template inválido")
            self.preview_panel.set_marker_count(0)
            self._set_status("Erro ao carregar")
            if show_errors:
                messagebox.showerror("Erro ao carregar", f"Não foi possível carregar o template:\n{exc}")

    def request_preview_update(self) -> None:
        if self._preview_job is not None:
            self.after_cancel(self._preview_job)
        self._preview_job = self.after(250, self._run_scheduled_preview)

    def _run_scheduled_preview(self) -> None:
        self._preview_job = None
        self.update_preview()

    def _get_reader(self) -> DOCXReader | None:
        if self.template_path is None:
            return None
        if self.reader is None:
            self.reader = DOCXReader(self.template_path)
        return self.reader

    def _build_replacements(self) -> dict[str, str]:
        values = self.form_panel.get_values()
        replacements = self.mapping_manager.build_replacements(values)
        reader = self._get_reader()
        if reader is not None:
            replacements.update(reader.build_literal_replacements(values))
        return replacements

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
        if path.suffix.lower() != ".docx":
            return "Selecione um arquivo Word no formato .docx."
        return None

    def close_app(self) -> None:
        if self._preview_job is not None:
            try:
                self.after_cancel(self._preview_job)
            except Exception:
                pass
            self._preview_job = None
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
