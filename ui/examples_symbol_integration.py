"""
Exemplo de integração do símbolo interno em diferentes contextos.
Mostra como aplicar o SymbolManager em diversos cenários.
"""

import customtkinter as ctk
from ui.symbol_manager import SymbolManager
from ui.theme import COLORS, font


class SidebarWithSymbol(ctk.CTkFrame):
    """Exemplo: Sidebar com símbolo interno no topo."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg2"], corner_radius=0, **kwargs)
        
        # Símbolo no topo (32x32)
        symbol = SymbolManager.get_symbol("sidebar", size=32)
        if symbol:
            symbol_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
            symbol_frame.pack(fill="x", padx=0, pady=(16, 8))
            
            ctk.CTkLabel(symbol_frame, image=symbol, text="").pack()
        
        # Brand text
        brand_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        brand_frame.pack(fill="x", padx=16, pady=(0, 16))
        
        ctk.CTkLabel(
            brand_frame,
            text="DocFill Pro",
            text_color=COLORS["text"],
            font=font(14, "bold"),
        ).pack(anchor="w")
        
        # Separador
        ctk.CTkFrame(self, fg_color=COLORS["border"], height=1, corner_radius=0).pack(fill="x", pady=12)
        
        # Conteúdo restante
        content = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        content.pack(fill="both", expand=True, padx=12, pady=12)


class EmptyStateWithSymbol(ctk.CTkFrame):
    """Exemplo: Empty state com símbolo semi-transparente."""
    
    def __init__(self, parent, title="Nenhum documento carregado", description="", **kwargs):
        super().__init__(parent, fg_color=COLORS["bg"], corner_radius=0, **kwargs)
        
        # Frame centralizado
        container = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        container.pack(fill="both", expand=True)
        container.pack_propagate(False)
        
        # Símbolo com opacidade reduzida (15%)
        symbol = SymbolManager.get_symbol_with_opacity("empty", opacity=0.15)
        if symbol:
            ctk.CTkLabel(container, image=symbol, text="").pack(expand=True)
        
        # Título
        ctk.CTkLabel(
            container,
            text=title,
            text_color=COLORS["text"],
            font=font(16, "bold"),
            anchor="center",
        ).pack(pady=(12, 4))
        
        # Descrição
        if description:
            ctk.CTkLabel(
                container,
                text=description,
                text_color=COLORS["text3"],
                font=font(11),
                anchor="center",
            ).pack(pady=(0, 12))


class LoadingStateWithSymbol(ctk.CTkFrame):
    """Exemplo: Loading state com símbolo animado."""
    
    def __init__(self, parent, message="Processando...", **kwargs):
        super().__init__(parent, fg_color=COLORS["bg"], corner_radius=0, **kwargs)
        
        container = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        container.pack(fill="both", expand=True)
        
        # Símbolo com animação suave (pulse)
        symbol = SymbolManager.get_symbol("loading", size=48)
        if symbol:
            self.symbol_label = ctk.CTkLabel(container, image=symbol, text="")
            self.symbol_label.pack(expand=True, pady=(0, 12))
            
            # Iniciar animação de fade
            self._animate_pulse()
        
        # Mensagem
        ctk.CTkLabel(
            container,
            text=message,
            text_color=COLORS["text2"],
            font=font(12),
        ).pack(pady=(0, 12))
    
    def _animate_pulse(self):
        """Animação de pulse suave."""
        # Implementação simplificada
        # Em produção, usar após_delay para animar continuamente
        pass


class HeaderWithSymbol(ctk.CTkFrame):
    """Exemplo: Header com símbolo pequeno."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg2"], corner_radius=0, height=48, **kwargs)
        self.grid_propagate(False)
        
        # Símbolo no header (20x20)
        symbol = SymbolManager.get_symbol("header", size=20)
        if symbol:
            ctk.CTkLabel(self, image=symbol, text="").grid(row=0, column=0, padx=(14, 8), sticky="ns")
        
        # Título
        ctk.CTkLabel(
            self,
            text="DocFill Pro",
            text_color=COLORS["text"],
            font=font(13, "bold"),
        ).grid(row=0, column=1, sticky="w")
        
        self.grid_columnconfigure(2, weight=1)


class PreviewPlaceholder(ctk.CTkFrame):
    """Exemplo: Preview vazio com símbolo."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg"], corner_radius=12, **kwargs)
        
        # Símbolo centralizado
        symbol = SymbolManager.get_symbol("empty", size=72)
        if symbol:
            container = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
            container.pack(fill="both", expand=True)
            
            ctk.CTkLabel(container, image=symbol, text="").pack(expand=True, pady=(20, 12))
        
        # Texto informativo
        ctk.CTkLabel(
            self,
            text="Selecione um documento para visualizar",
            text_color=COLORS["text3"],
            font=font(10),
        ).pack(pady=(0, 20))


# Teste rápido
if __name__ == "__main__":
    app = ctk.CTk()
    app.geometry("600x400")
    
    # Testar cada componente
    test_frame = ctk.CTkTabview(app)
    test_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Tab 1: Empty State
    empty_tab = test_frame.add("Empty State")
    EmptyStateWithSymbol(
        empty_tab,
        title="Nenhum documento carregado",
        description="Importe um modelo Word para começar."
    ).pack(fill="both", expand=True)
    
    # Tab 2: Loading
    loading_tab = test_frame.add("Loading")
    LoadingStateWithSymbol(loading_tab, "Analisando documento...").pack(fill="both", expand=True)
    
    # Tab 3: Preview
    preview_tab = test_frame.add("Preview")
    PreviewPlaceholder(preview_tab).pack(fill="both", expand=True, padx=20, pady=20)
    
    app.mainloop()
