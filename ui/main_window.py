from pathlib import Path

import customtkinter as ctk
from tkinter import filedialog, messagebox

from services.docx_reader import DOCXReader
from services.docx_writer import DOCXWriter
from services.mapping_manager import MappingManager
from ui.form_panel import FormPanel
from ui.preview_panel import PreviewPanel


class DocFillProApp(ctk.CTk):
    """Aplicativo principal DOCFILL PRO."""

    def __init__(self, initial_template: str | Path | None = None) -> None:
        super().__init__()

        self.title("DOCFILL PRO")
        self.geometry("1600x900")
        self.minsize(1300, 800)
        self.configure(fg_color="#071A12")

        self.template_path: Path | None = None
        self.output_folder: Path | None = None
        self.reader: DOCXReader | None = None
        self.template_suggestions: dict[str, str] = {}
        self._preview_job: str | None = None
        self.mapping_manager = MappingManager()
        self.logo_image = None

        self._build_ui()
        if initial_template:
            self.load_template(initial_template, show_errors=False)
        else:
            self.update_preview()
        self.protocol("WM_DELETE_WINDOW", self.close_app)

    def _build_ui(self) -> None:
        root = ctk.CTkFrame(self, fg_color="#071A12")
        root.pack(fill="both", expand=True, padx=18, pady=18)

        header = ctk.CTkFrame(root, fg_color="#071A12")
        header.pack(fill="x", pady=(0, 12))

        title_frame = ctk.CTkFrame(header, fg_color="#071A12")
        title_frame.pack(side="left", fill="x", expand=True)

        logo_path = Path(__file__).resolve().parent.parent / "assets" / "logo.png"
        logo_label = ctk.CTkLabel(title_frame, text="DOCFILL PRO", font=("Segoe UI", 28, "bold"), text_color="#F2FBF5")
        if logo_path.exists():
            try:
                from PIL import Image
                self.logo_image = ctk.CTkImage(light_image=Image.open(logo_path), size=(64, 64))
                logo_label = ctk.CTkLabel(title_frame, image=self.logo_image, text="")
            except Exception:
                logo_label = ctk.CTkLabel(title_frame, text="DOCFILL PRO", font=("Segoe UI", 28, "bold"), text_color="#F2FBF5")
        logo_label.pack(anchor="w")

        ctk.CTkLabel(title_frame, text="DOCFILL PRO", font=("Segoe UI", 26, "bold"), text_color="#F2FBF5").pack(anchor="w", pady=(8, 0))
        ctk.CTkLabel(title_frame, text="Documentos Word preenchidos com controle e preview em tempo real.", font=("Segoe UI", 13), text_color="#B7C9BC").pack(anchor="w", pady=(3, 0))

        status = ctk.CTkLabel(header, text="Status: pronto para carregar um template .docx", text_color="#B7C9BC", font=("Segoe UI", 12))
        status.pack(side="right", anchor="e")
        self.status_label = status

        toolbar = ctk.CTkFrame(root, fg_color="#0B2418", corner_radius=8)
        toolbar.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            toolbar,
            text="Arquivo Word",
            font=("Segoe UI", 14, "bold"),
            text_color="#F2FBF5",
        ).pack(side="left", padx=(14, 10), pady=12)

        ctk.CTkButton(
            toolbar,
            text="Adicionar Word (.docx)",
            fg_color="#22C55E",
            hover_color="#16A34A",
            text_color="#F2FBF5",
            width=190,
            command=self.select_template,
        ).pack(side="left", padx=6, pady=10)

        ctk.CTkButton(
            toolbar,
            text="Escolher Pasta",
            fg_color="#15803D",
            hover_color="#166534",
            text_color="#F2FBF5",
            width=150,
            command=self.select_output,
        ).pack(side="left", padx=6, pady=10)

        ctk.CTkButton(
            toolbar,
            text="Gerar Documento",
            fg_color="#22C55E",
            hover_color="#16A34A",
            text_color="#F2FBF5",
            width=170,
            command=self.generate_document,
        ).pack(side="left", padx=6, pady=10)

        toolbar_status = ctk.CTkFrame(toolbar, fg_color="transparent")
        toolbar_status.pack(side="right", padx=14, pady=8)

        self.toolbar_template_label = ctk.CTkLabel(
            toolbar_status,
            text="Word: nenhum arquivo",
            font=("Segoe UI", 11),
            text_color="#B7C9BC",
            anchor="e",
        )
        self.toolbar_template_label.pack(anchor="e")

        self.toolbar_output_label = ctk.CTkLabel(
            toolbar_status,
            text="Saída: escolher ao gerar",
            font=("Segoe UI", 11),
            text_color="#B7C9BC",
            anchor="e",
        )
        self.toolbar_output_label.pack(anchor="e", pady=(2, 0))

        self.tabview = ctk.CTkTabview(root, fg_color="#071A12", segmented_button_fg_color="#103522", segmented_button_selected_color="#22C55E", segmented_button_selected_hover_color="#16A34A")
        self.tabview.add("Documento")
        self.tabview.add("Mapeamento")
        self.tabview.pack(fill="both", expand=True)

        doc_tab = self.tabview.tab("Documento")
        doc_tab.grid_columnconfigure(0, weight=3, minsize=720)
        doc_tab.grid_columnconfigure(1, weight=2, minsize=460)
        doc_tab.grid_rowconfigure(0, weight=1)

        self.preview_panel = PreviewPanel(doc_tab)
        self.preview_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=0)

        self.form_panel = FormPanel(
            doc_tab,
            on_update=self.request_preview_update,
            callbacks={
                "select_template": self.select_template,
                "select_output": self.select_output,
                "generate": self.generate_document,
                "clear": self.clear_form,
            },
        )
        self.form_panel.grid(row=0, column=1, sticky="nsew")

        self._build_mapping_tab()

    def analyze_template_section(self) -> None:
        if not self.template_path:
            self.analysis_view.configure(state="normal")
            self.analysis_view.delete("1.0", "end")
            self.analysis_view.insert("1.0", "Selecione um template .docx para iniciar a análise.")
            self.analysis_view.configure(state="disabled")
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
                lines.extend(f"  • {marker}" for marker in analysis["placeholders"])
            else:
                lines.append("  • Nenhum marcador encontrado.")

            lines.append("\nÁreas identificadas:")
            if analysis["areas"]:
                lines.extend(f"  • {area}" for area in analysis["areas"])
            else:
                lines.append("  • Nenhuma área especial detectada.")

            self.analysis_view.configure(state="normal")
            self.analysis_view.delete("1.0", "end")
            self.analysis_view.insert("1.0", "\n".join(lines))
            self.analysis_view.configure(state="disabled")
            self.status_label.configure(text="Status: análise concluída")
        except Exception as exc:
            self.analysis_view.configure(state="normal")
            self.analysis_view.delete("1.0", "end")
            self.analysis_view.insert("1.0", f"Não foi possível analisar o template:\n{exc}")
            self.analysis_view.configure(state="disabled")
            self.status_label.configure(text="Status: erro na análise do template")

    def _build_mapping_tab(self) -> None:
        mapping_tab = self.tabview.tab("Mapeamento")
        mapping_tab.grid_columnconfigure(0, weight=1)
        mapping_tab.grid_rowconfigure(0, weight=1)

        wrapper = ctk.CTkFrame(mapping_tab, fg_color="#071A12")
        wrapper.pack(fill="both", expand=True, padx=18, pady=18)

        info_card = ctk.CTkFrame(wrapper, fg_color="#0B2418", corner_radius=8)
        info_card.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(info_card, text="Mapeamento", font=("Segoe UI", 18, "bold"), text_color="#F2FBF5", anchor="w").pack(anchor="w", padx=16, pady=(14, 4))
        ctk.CTkLabel(info_card, text="Cadastre marcadores extra e analise como o template está organizado por áreas.", font=("Segoe UI", 12), text_color="#B7C9BC", anchor="w").pack(anchor="w", padx=16, pady=(0, 14))

        analysis_card = ctk.CTkFrame(wrapper, fg_color="#0B2418", corner_radius=8)
        analysis_card.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(analysis_card, text="Área de Análise do Template", font=("Segoe UI", 14, "bold"), text_color="#F2FBF5", anchor="w").pack(anchor="w", padx=14, pady=(12, 6))
        ctk.CTkLabel(analysis_card, text="Selecione um template na aba Documento ou use o botão abaixo para detectar marcadores, parágrafos, tabelas, cabeçalhos e rodapés.", font=("Segoe UI", 12), text_color="#B7C9BC", anchor="w").pack(anchor="w", padx=14, pady=(0, 8))
        ctk.CTkButton(analysis_card, text="Analisar Template Atual", fg_color="#22C55E", hover_color="#16A34A", command=self.analyze_template_section).pack(fill="x", padx=14, pady=(0, 10))
        self.analysis_view = ctk.CTkTextbox(analysis_card, fg_color="#06140D", text_color="#F2FBF5", border_width=1, border_color="#22543D", font=("Segoe UI", 12), height=180)
        self.analysis_view.pack(fill="x", padx=14, pady=(0, 14))
        self.analysis_view.configure(state="disabled")

        form_card = ctk.CTkFrame(wrapper, fg_color="#0B2418", corner_radius=8)
        form_card.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(form_card, text="Adicionar marcador", font=("Segoe UI", 14, "bold"), text_color="#F2FBF5", anchor="w").pack(anchor="w", padx=14, pady=(12, 6))

        self.custom_marker = ctk.CTkEntry(form_card, placeholder_text="Ex.: TELEFONE", fg_color="#06140D", border_color="#22543D", text_color="#F2FBF5")
        self.custom_marker.pack(fill="x", padx=14, pady=6)
        self.custom_value = ctk.CTkEntry(form_card, placeholder_text="Valor do marcador", fg_color="#06140D", border_color="#22543D", text_color="#F2FBF5")
        self.custom_value.pack(fill="x", padx=14, pady=6)

        ctk.CTkButton(form_card, text="Salvar Marcador", fg_color="#22C55E", hover_color="#16A34A", command=self.save_mapping).pack(fill="x", padx=14, pady=(6, 12))

        list_card = ctk.CTkFrame(wrapper, fg_color="#0B2418", corner_radius=8)
        list_card.pack(fill="both", expand=True)
        ctk.CTkLabel(list_card, text="Marcadores cadastrados", font=("Segoe UI", 14, "bold"), text_color="#F2FBF5", anchor="w").pack(anchor="w", padx=14, pady=(12, 6))
        self.mapping_view = ctk.CTkTextbox(list_card, fg_color="#06140D", text_color="#F2FBF5", border_width=1, border_color="#22543D", font=("Segoe UI", 12))
        self.mapping_view.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        self.mapping_view.configure(state="disabled")

        self.refresh_mapping_view()

    def update_preview(self) -> None:
        if not self.template_path:
            self.preview_panel.set_text("Selecione um template .docx para visualizar o documento.")
            self.preview_panel.set_meta("Nenhum template carregado")
            self.status_label.configure(text="Status: selecione um template .docx")
            return

        try:
            reader = self._get_reader()
            if reader is None:
                return
            replacements = self._build_replacements()
            text = reader.extract_text(replacements)
            analysis = reader.analyze_template()
            self.preview_panel.set_text(text)
            self.preview_panel.set_meta(
                f"{self.template_path.name} | {len(text):,} caracteres | "
                f"{len(analysis['placeholders'])} marcadores | "
                f"{len(self.template_suggestions)} campos detectados"
            )
            self.status_label.configure(text=f"Status: preview atualizado com {len(replacements)} substituições")
        except Exception as exc:
            self.preview_panel.set_text(f"Não foi possível gerar o preview: {exc}")
            self.preview_panel.set_meta("Erro ao ler o template")
            self.status_label.configure(text="Status: erro na leitura do template")

    def select_template(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Adicionar arquivo Word",
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
            self.form_panel.set_output_info(str(self.output_folder))
            self.toolbar_output_label.configure(text=f"Saída: {self.output_folder.name}")
            self.status_label.configure(text=f"Status: pasta de saída definida - {folder}")

    def clear_form(self) -> None:
        self.form_panel.clear()
        self.status_label.configure(text="Status: campos limpos")

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

        if not output_folder:
            return

        replacements = self._build_replacements()
        comprador = values.get("{{COMPRADOR}}", "").strip()
        sanitized_name = self._sanitize_filename(comprador)
        output_path = Path(output_folder) / f"DECLARACAO - {sanitized_name}.docx"
        output_path = self._next_available_path(output_path)

        try:
            writer = DOCXWriter()
            writer.generate(self.template_path, output_path, replacements)
            messagebox.showinfo("Sucesso", f"Documento gerado com sucesso em:\n{output_path}")
            self.status_label.configure(text=f"Status: documento gerado - {output_path.name}")
        except Exception as exc:
            messagebox.showerror("Erro ao gerar", f"Não foi possível gerar o arquivo: {exc}")

    def save_mapping(self) -> None:
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
        data = self.mapping_manager.load()
        self.mapping_view.configure(state="normal")
        self.mapping_view.delete("1.0", "end")
        if not data:
            self.mapping_view.insert("1.0", "Nenhum marcador adicional cadastrado.")
        else:
            lines = [f"{key} = {value}" for key, value in sorted(data.items())]
            self.mapping_view.insert("1.0", "\n".join(lines))
        self.mapping_view.configure(state="disabled")

    def load_template(self, file_path: str | Path, show_errors: bool = True) -> None:
        path = Path(file_path)
        if not path.exists():
            message = f"Template não encontrado:\n{path}"
            self.status_label.configure(text="Status: template não encontrado")
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
            self.preview_panel.set_meta("Arquivo Word não carregado")
            self.form_panel.set_template_info("nenhum selecionado")
            self.toolbar_template_label.configure(text="Word: nenhum arquivo")
            self.status_label.configure(text="Status: arquivo Word não suportado")
            if show_errors:
                messagebox.showerror("Arquivo Word não suportado", validation_error)
            return

        self.template_path = path
        self.reader = DOCXReader(path)
        try:
            analysis = self.reader.analyze_template()
            self.template_suggestions = self.reader.suggest_values()
            detected = self.form_panel.set_values(self.template_suggestions, only_empty=True)
            self.form_panel.set_template_info(path.name)
            self.toolbar_template_label.configure(text=f"Word: {path.name}")
            if self.output_folder is not None:
                self.form_panel.set_output_info(str(self.output_folder))
                self.toolbar_output_label.configure(text=f"Saída: {self.output_folder.name}")
            self.update_preview()
            self.analyze_template_section()

            if analysis["placeholders"]:
                self.status_label.configure(text=f"Status: template carregado com {len(analysis['placeholders'])} marcadores")
            elif self.template_suggestions:
                self.status_label.configure(text=f"Status: modelo sem marcadores; {detected} campos detectados")
            else:
                self.status_label.configure(text="Status: template carregado sem marcadores detectáveis")
        except Exception as exc:
            self.template_suggestions = {}
            self.preview_panel.set_text(f"Não foi possível carregar o template:\n{exc}")
            self.preview_panel.set_meta("Template inválido ou ilegível")
            self.status_label.configure(text="Status: erro ao carregar template")
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
