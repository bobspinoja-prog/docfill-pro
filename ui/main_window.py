from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from services.docx_reader import DOCXReader
from services.docx_writer import DOCXWriter
from services.mapping_manager import MappingManager
from ui.form_panel import FormPanel
from ui.preview_panel import PreviewPanel


class DocFillProApp(ctk.CTk):
    """Aplicativo principal DOCFILL PRO."""

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
    INPUT = "#07130D"
    INPUT_BORDER = "#315A43"

    def __init__(self, initial_template: str | Path | None = None) -> None:
        super().__init__()

        self.title("DOCFILL PRO")
        self.geometry("1600x900")
        self.minsize(1300, 800)
        self.configure(fg_color=self.BG)

        self.template_path: Path | None = None
        self.output_folder: Path | None = None
        self.reader: DOCXReader | None = None
        self.template_suggestions: dict[str, str] = {}
        self._preview_job: str | None = None
        self.mapping_manager = MappingManager()
        self.logo_image = None
        self.footer_logo_image = None
        self.mapping_window = None
        self.analysis_view = None
        self.mapping_view = None
        self.custom_marker = None
        self.custom_value = None

        self._build_ui()
        if initial_template:
            self.load_template(initial_template, show_errors=False)
        else:
            self.update_preview()
        self.protocol("WM_DELETE_WINDOW", self.close_app)

    def _build_ui(self) -> None:
        root = ctk.CTkFrame(self, fg_color=self.BG)
        root.pack(fill="both", expand=True, padx=16, pady=12)
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(1, weight=1)

        self._build_header(root)
        self._build_body(root)
        self._build_footer(root)

    def _build_header(self, master: ctk.CTkFrame) -> None:
        header = ctk.CTkFrame(master, fg_color=self.BG, height=90)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header.grid_columnconfigure(1, weight=1)
        header.grid_propagate(False)

        logo_frame = ctk.CTkFrame(header, width=62, height=62, fg_color="#15803D", corner_radius=31)
        logo_frame.grid(row=0, column=0, rowspan=2, padx=(0, 16), pady=14)
        logo_frame.grid_propagate(False)

        logo_path = Path(__file__).resolve().parent.parent / "assets" / "logo.png"
        if logo_path.exists():
            try:
                from PIL import Image

                self.logo_image = ctk.CTkImage(Image.open(logo_path), size=(48, 48))
                ctk.CTkLabel(logo_frame, image=self.logo_image, text="").place(relx=0.5, rely=0.5, anchor="center")
            except Exception:
                ctk.CTkLabel(logo_frame, text="DF", font=("Segoe UI", 18, "bold"), text_color=self.TEXT).place(relx=0.5, rely=0.5, anchor="center")
        else:
            ctk.CTkLabel(logo_frame, text="DF", font=("Segoe UI", 18, "bold"), text_color=self.TEXT).place(relx=0.5, rely=0.5, anchor="center")

        brand = ctk.CTkFrame(header, fg_color="transparent")
        brand.grid(row=0, column=1, rowspan=2, sticky="w", pady=12)

        brand_line = ctk.CTkFrame(brand, fg_color="transparent")
        brand_line.pack(anchor="w")
        ctk.CTkLabel(
            brand_line,
            text="DocFill Pro",
            font=("Segoe UI", 29, "bold"),
            text_color=self.TEXT,
        ).pack(side="left")
        ctk.CTkFrame(brand_line, width=1, height=32, fg_color=self.BORDER).pack(side="left", padx=22)
        ctk.CTkLabel(
            brand_line,
            text="Preencha seus documentos com agilidade e segurança",
            font=("Segoe UI", 13),
            text_color=self.MUTED,
        ).pack(side="left")

        actions = ctk.CTkFrame(header, fg_color="transparent")
        actions.grid(row=0, column=2, rowspan=2, sticky="e", pady=18)
        for text, command in (
            ("Tema", self.show_theme_info),
            ("Ajustes", self.open_settings),
            ("Sobre", self.show_about),
        ):
            ctk.CTkButton(
                actions,
                text=text,
                width=86,
                height=34,
                fg_color="transparent",
                hover_color=self.CARD,
                border_width=0,
                text_color=self.MUTED,
                command=command,
            ).pack(side="left", padx=4)

    def _build_body(self, master: ctk.CTkFrame) -> None:
        body = ctk.CTkFrame(master, fg_color=self.BG)
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=56, minsize=710)
        body.grid_columnconfigure(1, weight=44, minsize=520)
        body.grid_rowconfigure(0, weight=1)

        self.preview_panel = PreviewPanel(body, on_refresh=self.update_preview)
        self.preview_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

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
        self.form_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

    def _build_footer(self, master: ctk.CTkFrame) -> None:
        footer = ctk.CTkFrame(master, fg_color=self.BG, height=34)
        footer.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        footer.grid_columnconfigure(1, weight=1)
        footer.grid_propagate(False)

        logo_path = Path(__file__).resolve().parent.parent / "assets" / "logo.png"
        try:
            from PIL import Image

            self.footer_logo_image = ctk.CTkImage(Image.open(logo_path), size=(20, 20))
            ctk.CTkLabel(footer, image=self.footer_logo_image, text="").grid(row=0, column=0, padx=(0, 8), pady=6)
        except Exception:
            ctk.CTkLabel(footer, text="DF", text_color=self.GREEN_NEON, font=("Segoe UI", 11, "bold")).grid(row=0, column=0, padx=(0, 8))

        ctk.CTkLabel(
            footer,
            text="DocFill Pro   v1.0.0",
            text_color=self.TEXT,
            font=("Segoe UI", 12),
        ).grid(row=0, column=1, sticky="w")

        self.status_label = ctk.CTkLabel(
            footer,
            text="Pronto",
            text_color=self.GREEN_NEON,
            font=("Segoe UI", 13),
        )
        self.status_label.grid(row=0, column=2, sticky="e", padx=(0, 4))

    def open_settings(self) -> None:
        if self.mapping_window is not None and self.mapping_window.winfo_exists():
            self.mapping_window.deiconify()
            self.mapping_window.lift()
            self.refresh_mapping_view()
            self.analyze_template_section()
            return

        window = ctk.CTkToplevel(self)
        window.title("DOCFILL PRO - Ajustes e Mapeamento")
        window.geometry("900x700")
        window.minsize(760, 560)
        window.configure(fg_color=self.BG)
        window.protocol("WM_DELETE_WINDOW", window.withdraw)
        window.grid_columnconfigure(0, weight=1)
        window.grid_rowconfigure(1, weight=1)
        self.mapping_window = window

        ctk.CTkLabel(
            window,
            text="Mapeamento",
            font=("Segoe UI", 22, "bold"),
            text_color=self.GREEN_NEON,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 4))

        wrapper = ctk.CTkFrame(window, fg_color=self.SURFACE, corner_radius=14, border_width=1, border_color=self.BORDER)
        wrapper.grid(row=1, column=0, sticky="nsew", padx=18, pady=18)
        wrapper.grid_columnconfigure(0, weight=1)
        wrapper.grid_rowconfigure(2, weight=1)

        analysis_card = ctk.CTkFrame(wrapper, fg_color=self.PANEL, corner_radius=12, border_width=1, border_color=self.BORDER)
        analysis_card.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 10))
        analysis_card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(analysis_card, text="Análise do Template", font=("Segoe UI", 14, "bold"), text_color=self.GREEN_NEON, anchor="w").grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 6))
        ctk.CTkButton(analysis_card, text="Analisar Template Atual", fg_color=self.GREEN, hover_color=self.GREEN_HOVER, command=self.analyze_template_section).grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 8))
        self.analysis_view = ctk.CTkTextbox(analysis_card, fg_color=self.INPUT, text_color=self.TEXT, border_width=1, border_color=self.INPUT_BORDER, font=("Segoe UI", 12), height=150)
        self.analysis_view.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 14))
        self.analysis_view.configure(state="disabled")

        form_card = ctk.CTkFrame(wrapper, fg_color=self.PANEL, corner_radius=12, border_width=1, border_color=self.BORDER)
        form_card.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 10))
        form_card.grid_columnconfigure(0, weight=1)
        form_card.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(form_card, text="Adicionar marcador", font=("Segoe UI", 14, "bold"), text_color=self.GREEN_NEON, anchor="w").grid(row=0, column=0, columnspan=2, sticky="ew", padx=14, pady=(12, 6))
        self.custom_marker = ctk.CTkEntry(form_card, placeholder_text="Ex.: TELEFONE", fg_color=self.INPUT, border_color=self.INPUT_BORDER, text_color=self.TEXT)
        self.custom_marker.grid(row=1, column=0, sticky="ew", padx=(14, 6), pady=(0, 12))
        self.custom_value = ctk.CTkEntry(form_card, placeholder_text="Valor do marcador", fg_color=self.INPUT, border_color=self.INPUT_BORDER, text_color=self.TEXT)
        self.custom_value.grid(row=1, column=1, sticky="ew", padx=(6, 14), pady=(0, 12))
        ctk.CTkButton(form_card, text="Salvar Marcador", fg_color=self.GREEN, hover_color=self.GREEN_HOVER, command=self.save_mapping).grid(row=2, column=0, columnspan=2, sticky="ew", padx=14, pady=(0, 14))

        list_card = ctk.CTkFrame(wrapper, fg_color=self.PANEL, corner_radius=12, border_width=1, border_color=self.BORDER)
        list_card.grid(row=2, column=0, sticky="nsew", padx=14, pady=(0, 14))
        list_card.grid_columnconfigure(0, weight=1)
        list_card.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(list_card, text="Marcadores cadastrados", font=("Segoe UI", 14, "bold"), text_color=self.GREEN_NEON, anchor="w").grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 6))
        self.mapping_view = ctk.CTkTextbox(list_card, fg_color=self.INPUT, text_color=self.TEXT, border_width=1, border_color=self.INPUT_BORDER, font=("Segoe UI", 12))
        self.mapping_view.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
        self.mapping_view.configure(state="disabled")

        self.refresh_mapping_view()
        self.analyze_template_section()

    def show_theme_info(self) -> None:
        messagebox.showinfo("Tema", "Tema verde premium ativo.")

    def show_about(self) -> None:
        messagebox.showinfo("Sobre", "DocFill Pro v1.0.0\nPreenchimento profissional de documentos Word.")

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
            self.status_label.configure(text="Análise concluída")
        except Exception as exc:
            self._set_textbox(self.analysis_view, f"Não foi possível analisar o template:\n{exc}")
            self.status_label.configure(text="Erro na análise")

    def update_preview(self) -> None:
        if not self.template_path:
            self.preview_panel.set_model_name("Nenhum modelo")
            self.preview_panel.set_marker_count(0)
            self.preview_panel.set_text("Selecione um template .docx para visualizar o documento.")
            self.status_label.configure(text="Pronto")
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
            self.status_label.configure(text="Pronto")
        except Exception as exc:
            self.preview_panel.set_text(f"Não foi possível gerar o preview: {exc}")
            self.preview_panel.set_marker_count(0)
            self.status_label.configure(text="Erro no preview")

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
            self.status_label.configure(text="Pasta definida")

    def clear_form(self) -> None:
        self.form_panel.clear()
        self.status_label.configure(text="Campos limpos")

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

        replacements = self._build_replacements()
        comprador = values.get("{{COMPRADOR}}", "").strip()
        sanitized_name = self._sanitize_filename(comprador)
        output_path = self._next_available_path(Path(output_folder) / f"DECLARACAO - {sanitized_name}.docx")

        try:
            writer = DOCXWriter()
            writer.generate(self.template_path, output_path, replacements)
            messagebox.showinfo("Sucesso", f"Documento gerado com sucesso em:\n{output_path}")
            self.status_label.configure(text="Documento gerado")
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
            self.status_label.configure(text="Template não encontrado")
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
            self.status_label.configure(text="Arquivo não suportado")
            if show_errors:
                messagebox.showerror("Arquivo Word não suportado", validation_error)
            return

        self.template_path = path
        self.reader = DOCXReader(path)
        try:
            analysis = self.reader.analyze_template()
            self.template_suggestions = self.reader.suggest_values()
            detected = self.form_panel.set_values(self.template_suggestions, only_empty=True)
            self.update_preview()
            self.analyze_template_section()

            if analysis["placeholders"]:
                self.status_label.configure(text=f"{len(analysis['placeholders'])} marcadores")
            elif self.template_suggestions:
                self.status_label.configure(text=f"{detected} campos detectados")
            else:
                self.status_label.configure(text="Template carregado")
        except Exception as exc:
            self.template_suggestions = {}
            self.preview_panel.set_text(f"Não foi possível carregar o template:\n{exc}")
            self.preview_panel.set_model_name("Template inválido")
            self.preview_panel.set_marker_count(0)
            self.status_label.configure(text="Erro ao carregar")
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
        self.destroy()

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
