import customtkinter as ctk


class PreviewPanel(ctk.CTkFrame):
    """Painel de visualização do documento preenchido."""

    def __init__(self, master: ctk.CTkFrame) -> None:
        super().__init__(master, fg_color="#0B2418", corner_radius=8)
        self.pack_propagate(False)

        self.title = ctk.CTkLabel(
            self,
            text="Visualização do Documento",
            font=("Segoe UI", 18, "bold"),
            text_color="#F2FBF5",
            anchor="w",
        )
        self.title.pack(anchor="w", padx=18, pady=(18, 6))

        self.meta = ctk.CTkLabel(
            self,
            text="Nenhum template carregado",
            font=("Segoe UI", 11),
            text_color="#B7C9BC",
            anchor="w",
        )
        self.meta.pack(anchor="w", padx=18, pady=(0, 8))

        self.preview = ctk.CTkTextbox(
            self,
            width=620,
            height=680,
            fg_color="#06140D",
            text_color="#F2FBF5",
            border_width=1,
            border_color="#22543D",
            activate_scrollbars=True,
            font=("Segoe UI", 13),
        )
        self.preview.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        self.preview.configure(state="disabled")

    def set_text(self, text: str) -> None:
        self.preview.configure(state="normal")
        self.preview.delete("1.0", "end")
        self.preview.insert("1.0", text or "Selecione um template para visualizar o conteúdo do documento.")
        self.preview.configure(state="disabled")

    def set_meta(self, text: str) -> None:
        self.meta.configure(text=text)
