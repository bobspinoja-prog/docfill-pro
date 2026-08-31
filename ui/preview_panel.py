import math
import re
import tkinter as tk

import customtkinter as ctk
from PIL import ImageTk

from ui.i18n import t
from ui.symbol_manager import SymbolManager
from ui.theme import COLORS, font, symbol_font


class PreviewPanel(ctk.CTkFrame):
    """Painel de preview com folha A4 centralizada."""

    ZOOM_STEPS = [60, 75, 90, 100, 110, 125, 150]
    PAGE_BASE_WIDTH = 620
    PAGE_RATIO = 1.414
    PAGE_PADDING_X = 48
    PAGE_PADDING_TOP = 40
    PAGE_PADDING_BOTTOM = 80

    def __init__(self, master: ctk.CTkFrame, on_refresh=None, on_pdf_area_selected=None) -> None:
        super().__init__(
            master,
            fg_color=COLORS["bg2"],
            corner_radius=0,
            border_width=0,
        )
        self.on_refresh = on_refresh
        self.on_pdf_area_selected = on_pdf_area_selected
        self.zoom_percent = 100
        self.marker_count = 0
        self._content = ""
        self._mode = "text"
        self._empty_state = True
        self._empty_symbol_image = SymbolManager.get_symbol_with_opacity("empty", opacity=0.18, size=72)
        self._empty_symbol_widget = None
        self._loading_symbol_images = [
            SymbolManager.get_symbol_with_opacity("loading", opacity=0.36, size=48),
            SymbolManager.get_symbol_with_opacity("loading", opacity=0.62, size=48),
        ]
        self._loading_symbol_widget = None
        self._loading_job = None
        self._loading_symbol_index = 0
        self._pdf_pages = []
        self._pdf_areas = []
        self._pdf_values: dict[str, str] = {}
        self._pdf_photo_images = []
        self._pdf_page_items: list[dict] = []
        self._pdf_selection_start = None
        self._pdf_selection_item = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_header()
        self._build_toolbar()
        self._build_preview()
        self._build_footer()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color=COLORS["bg2"], corner_radius=0)
        header.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 8))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header,
            text="▤",
            width=22,
            text_color=COLORS["green3"],
            font=symbol_font(18, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=(0, 8))

        ctk.CTkLabel(
            header,
            text=t("preview_title"),
            text_color=COLORS["text"],
            font=font(13, "bold"),
            anchor="w",
        ).grid(row=0, column=1, sticky="ew")

        ctk.CTkLabel(
            header,
            text=t("preview_hint"),
            text_color=COLORS["text3"],
            font=font(10),
            anchor="e",
        ).grid(row=0, column=2, sticky="e", padx=(10, 0))

    def _build_toolbar(self) -> None:
        toolbar = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg3"],
            corner_radius=8,
            border_width=1,
            border_color=COLORS["border"],
        )
        toolbar.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 10))
        toolbar.grid_columnconfigure(1, weight=1)

        file_badge = ctk.CTkFrame(toolbar, fg_color=COLORS["bg4"], corner_radius=6)
        file_badge.grid(row=0, column=0, sticky="w", padx=(10, 8), pady=9)
        file_badge.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            file_badge,
            text="▣",
            width=28,
            text_color=COLORS["green3"],
            font=symbol_font(15, "bold"),
        ).grid(row=0, column=0, rowspan=2, sticky="nsw", padx=(8, 7), pady=6)

        ctk.CTkLabel(
            file_badge,
            text=t("preview_model"),
            text_color=COLORS["text3"],
            font=font(9, "bold"),
            anchor="w",
        ).grid(row=0, column=1, sticky="ew", padx=(0, 12), pady=(6, 0))

        self.model_label = ctk.CTkLabel(
            file_badge,
            text=t("preview_none"),
            text_color=COLORS["text2"],
            font=font(11),
            anchor="w",
        )
        self.model_label.grid(row=1, column=1, sticky="ew", padx=(0, 12), pady=(0, 6))

        zoom_group = ctk.CTkFrame(toolbar, fg_color=COLORS["bg2"], corner_radius=6, border_width=1, border_color=COLORS["border2"])
        zoom_group.grid(row=0, column=2, sticky="e", padx=(8, 8), pady=9)
        for col in range(3):
            zoom_group.grid_columnconfigure(col, weight=0)

        ctk.CTkButton(
            zoom_group,
            text="−",
            width=30,
            height=28,
            fg_color="transparent",
            hover_color=COLORS["bg4"],
            text_color=COLORS["green3"],
            font=font(14, "bold"),
            command=self._zoom_out,
        ).grid(row=0, column=0, padx=(2, 0), pady=2)

        self.zoom_label = ctk.CTkLabel(
            zoom_group,
            text="100%",
            width=48,
            text_color=COLORS["text"],
            font=font(11, "bold"),
        )
        self.zoom_label.grid(row=0, column=1, padx=2, pady=2)

        ctk.CTkButton(
            zoom_group,
            text="+",
            width=30,
            height=28,
            fg_color="transparent",
            hover_color=COLORS["bg4"],
            text_color=COLORS["green3"],
            font=font(14, "bold"),
            command=self._zoom_in,
        ).grid(row=0, column=2, padx=(0, 2), pady=2)

        ctk.CTkButton(
            toolbar,
            text=t("preview_refresh"),
            width=104,
            height=32,
            fg_color="transparent",
            hover_color=COLORS["bg4"],
            text_color=COLORS["green4"],
            border_width=1,
            border_color=COLORS["border2"],
            corner_radius=6,
            font=font(11, "bold"),
            command=self.on_refresh,
        ).grid(row=0, column=3, sticky="e", padx=(0, 10), pady=9)

    def _build_preview(self) -> None:
        viewer = ctk.CTkFrame(self, fg_color=COLORS["bg"], corner_radius=0)
        viewer.grid(row=2, column=0, sticky="nsew", padx=14, pady=(0, 0))
        viewer.grid_columnconfigure(0, weight=1)
        viewer.grid_rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(viewer, bg=COLORS["bg"], highlightthickness=0, bd=0)
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=(10, 2), pady=10)

        self.scrollbar = ctk.CTkScrollbar(
            viewer,
            orientation="vertical",
            command=self.canvas.yview,
            width=12,
            fg_color=COLORS["bg"],
            button_color="#64748B",
            button_hover_color=COLORS["text3"],
            corner_radius=8,
        )
        self.scrollbar.grid(row=0, column=1, sticky="ns", padx=(0, 8), pady=10)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.shadow = ctk.CTkFrame(self.canvas, fg_color="#D9E2E8", corner_radius=3)
        self.page = ctk.CTkFrame(
            self.shadow,
            fg_color="#FFFFFF",
            corner_radius=2,
            border_width=1,
            border_color="#E2E8F0",
        )
        self.page.grid(row=0, column=0, sticky="nsew", padx=(0, 3), pady=(0, 3))
        self.page.grid_columnconfigure(0, weight=1)
        self.page.grid_rowconfigure(0, weight=1)

        self.text = tk.Text(
            self.page,
            bg="#FFFFFF",
            fg="#020617",
            insertbackground="#020617",
            relief="flat",
            borderwidth=0,
            wrap="word",
            padx=self.PAGE_PADDING_X,
            pady=self.PAGE_PADDING_TOP,
            font=("Segoe UI", 11),
            spacing1=1,
            spacing2=1,
            spacing3=6,
            cursor="arrow",
            takefocus=False,
        )
        self.text.grid(row=0, column=0, sticky="nsew")
        self.text.tag_configure("marker", foreground="#16A34A", background="#F0FDF4", font=("Segoe UI", 11, "bold"))
        self.text.tag_configure("empty", foreground=COLORS["text3"], justify="center", font=("Segoe UI", 12))
        self.text.configure(state="disabled")

        self.page_window = self.canvas.create_window(0, 18, window=self.shadow, anchor="n")
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<ButtonPress-1>", self._on_pdf_press)
        self.canvas.bind("<B1-Motion>", self._on_pdf_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_pdf_release)
        self.text.bind("<MouseWheel>", self._on_mousewheel)
        self.page.bind("<MouseWheel>", self._on_mousewheel)
        self.shadow.bind("<MouseWheel>", self._on_mousewheel)

    def _build_footer(self) -> None:
        footer = ctk.CTkFrame(self, fg_color=COLORS["bg3"], corner_radius=8)
        footer.grid(row=3, column=0, sticky="ew", padx=14, pady=(8, 10))
        footer.grid_columnconfigure(5, weight=1)

        self.page_label = ctk.CTkLabel(footer, text="Página 1 de 1", text_color=COLORS["text2"], font=font(10))
        self.page_label.grid(row=0, column=0, padx=(10, 7), pady=6)

        ctk.CTkLabel(footer, text="•", text_color=COLORS["text3"], font=font(10, "bold")).grid(row=0, column=1, padx=2, pady=6)

        self.words_label = ctk.CTkLabel(footer, text="0 palavras", text_color=COLORS["text2"], font=font(10))
        self.words_label.grid(row=0, column=2, padx=7, pady=6)

        ctk.CTkLabel(footer, text="•", text_color=COLORS["text3"], font=font(10, "bold")).grid(row=0, column=3, padx=2, pady=6)

        self.chars_label = ctk.CTkLabel(footer, text="0 caracteres", text_color=COLORS["text2"], font=font(10))
        self.chars_label.grid(row=0, column=4, padx=7, pady=6)

        self.marker_badge = ctk.CTkLabel(
            footer,
            text="0 " + t("preview_marker_badge"),
            fg_color="#0E7A34",
            text_color=COLORS["green4"],
            corner_radius=5,
            font=font(10, "bold"),
        )
        self.marker_badge.grid(row=0, column=6, padx=10, pady=6)

    def set_text(self, text: str) -> None:
        self._mode = "text"
        self._clear_pdf_canvas()
        self.canvas.itemconfigure(self.page_window, state="normal")
        self._stop_loading()
        content = text or t("preview_empty")
        self._empty_state = not bool(text) or content.rstrip(".") == t("preview_empty")
        self._content = content

        self.text.configure(state="normal")
        if self._empty_symbol_widget is not None:
            self._empty_symbol_widget.destroy()
            self._empty_symbol_widget = None
        self.text.delete("1.0", "end")

        if self._empty_state:
            self.text.insert("1.0", "\n\n\n")
            if self._empty_symbol_image is not None:
                self._empty_symbol_widget = ctk.CTkLabel(
                    self.text,
                    image=self._empty_symbol_image,
                    text="",
                    fg_color="#FFFFFF",
                )
                self.text.window_create("end", window=self._empty_symbol_widget)
                self.text.insert("end", "\n\n" + t("preview_empty") + "\n" + t("preview_empty_hint"))
            else:
                self.text.insert("end", "▤\n\n" + t("preview_empty") + "\n" + t("preview_empty_hint"))
            self.text.tag_add("empty", "1.0", "end")
        else:
            self.text.insert("1.0", content)
            self._highlight_markers(content)

        self.text.configure(state="disabled")
        self._update_counts(content)
        self.after_idle(self._update_page_geometry)
        self.after(80, self._update_page_geometry)

    def set_loading(self, message: str) -> None:
        self._mode = "text"
        self._clear_pdf_canvas()
        self.canvas.itemconfigure(self.page_window, state="normal")
        self._empty_state = True
        self._content = message
        self.text.configure(state="normal")
        if self._empty_symbol_widget is not None:
            self._empty_symbol_widget.destroy()
            self._empty_symbol_widget = None
        if self._loading_symbol_widget is not None:
            self._loading_symbol_widget.destroy()
            self._loading_symbol_widget = None
        self.text.delete("1.0", "end")
        self.text.insert("1.0", "\n\n\n")

        loading_image = self._current_loading_symbol()
        if loading_image is not None:
            self._loading_symbol_widget = ctk.CTkLabel(
                self.text,
                image=loading_image,
                text="",
                fg_color="#FFFFFF",
            )
            self.text.window_create("end", window=self._loading_symbol_widget)
            self.text.insert("end", "\n\n" + message)
            self._pulse_loading_symbol()
        else:
            self.text.insert("end", "▤\n\n" + message)

        self.text.tag_add("empty", "1.0", "end")
        self.text.configure(state="disabled")
        self._update_counts(message)
        self.after_idle(self._update_page_geometry)
        self.after(80, self._update_page_geometry)

    def set_pdf_pages(self, pages: list, areas: list | None = None, values: dict[str, str] | None = None) -> None:
        self._stop_loading()
        self._mode = "pdf"
        self._empty_state = False
        self._pdf_pages = list(pages)
        self._pdf_areas = list(areas or [])
        self._pdf_values = dict(values or {})
        self.canvas.itemconfigure(self.page_window, state="hidden")
        self._render_pdf_canvas()
        page_count = len(self._pdf_pages)
        block_count = sum(len(getattr(page, "blocks", []) or []) for page in self._pdf_pages)
        area_count = len(self._pdf_areas)
        self.page_label.configure(text=f"PDF: {page_count} pagina(s)")
        self.words_label.configure(text=f"{block_count} blocos")
        self.chars_label.configure(text=f"{area_count} areas marcadas")

    def set_meta(self, text: str) -> None:
        if text and " | " in text:
            self.set_model_name(text.split(" | ", 1)[0])

    def set_model_name(self, name: str) -> None:
        label = name or t("preview_none")
        if len(label) > 54:
            label = f"...{label[-51:]}"
        self.model_label.configure(text=label)

    def set_marker_count(self, count: int) -> None:
        self.marker_count = max(0, count)
        self.marker_badge.configure(text=f"{self.marker_count} " + t("preview_marker_badge"))

    def _highlight_markers(self, content: str) -> None:
        self.text.tag_remove("marker", "1.0", "end")
        for match in re.finditer(r"\{\{[^{}]+\}\}", content):
            self.text.tag_add("marker", f"1.0+{match.start()}c", f"1.0+{match.end()}c")

    def _clear_pdf_canvas(self) -> None:
        self.canvas.delete("pdf")
        self.canvas.delete("pdf_selection")
        self._pdf_photo_images = []
        self._pdf_page_items = []
        self._pdf_selection_start = None
        self._pdf_selection_item = None

    def _render_pdf_canvas(self) -> None:
        if self._mode != "pdf":
            return
        self.update_idletasks()
        self.canvas.delete("pdf")
        self.canvas.delete("pdf_selection")
        self._pdf_photo_images = []
        self._pdf_page_items = []

        canvas_width = max(self.canvas.winfo_width(), 500)
        y = 18
        page_gap = 26
        max_width = canvas_width
        for page in self._pdf_pages:
            image = getattr(page, "image", None)
            if image is None:
                continue
            photo = ImageTk.PhotoImage(image)
            self._pdf_photo_images.append(photo)
            image_width = int(image.width)
            image_height = int(image.height)
            x = max((canvas_width - image_width) // 2, 24)
            self.canvas.create_rectangle(
                x + 5,
                y + 6,
                x + image_width + 5,
                y + image_height + 6,
                fill="#D9E2E8",
                outline="",
                tags=("pdf", "pdf_shadow"),
            )
            self.canvas.create_image(x, y, anchor="nw", image=photo, tags=("pdf", "pdf_page"))
            self.canvas.create_rectangle(
                x,
                y,
                x + image_width,
                y + image_height,
                outline="#CBD5E1",
                width=1,
                tags=("pdf", "pdf_page_border"),
            )
            page_info = {
                "page_index": getattr(page, "page_index", 0),
                "x": x,
                "y": y,
                "image_width": image_width,
                "image_height": image_height,
                "pdf_width": float(getattr(page, "width", image_width) or image_width),
                "pdf_height": float(getattr(page, "height", image_height) or image_height),
                "blocks": list(getattr(page, "blocks", []) or []),
            }
            self._pdf_page_items.append(page_info)
            self._draw_pdf_blocks(page_info)
            self._draw_pdf_areas(page_info)
            y += image_height + page_gap
            max_width = max(max_width, x + image_width + 40)

        self.canvas.configure(scrollregion=(0, 0, max_width, max(y, self.canvas.winfo_height())))

    def _draw_pdf_blocks(self, page_info: dict) -> None:
        for block in page_info.get("blocks", []):
            rect = self._pdf_rect_to_canvas(page_info, getattr(block, "rect", (0, 0, 0, 0)))
            if rect is None:
                continue
            x0, y0, x1, y1 = rect
            if x1 - x0 < 4 or y1 - y0 < 4:
                continue
            self.canvas.create_rectangle(
                x0,
                y0,
                x1,
                y1,
                outline="#86EFAC",
                dash=(2, 3),
                width=1,
                tags=("pdf", "pdf_block"),
            )

    def _draw_pdf_areas(self, page_info: dict) -> None:
        for area in self._pdf_areas:
            marker = self._area_marker(area)
            if self._area_page_index(area) != page_info.get("page_index"):
                continue
            rect = self._pdf_rect_to_canvas(page_info, self._area_rect(area))
            if rect is None:
                continue
            x0, y0, x1, y1 = rect
            label = self._marker_label(marker)
            self.canvas.create_rectangle(
                x0,
                y0,
                x1,
                y1,
                outline="#F59E0B",
                width=2,
                tags=("pdf", "pdf_manual_area"),
            )
            self.canvas.create_text(
                x0 + 4,
                max(y0 - 14, page_info["y"] + 8),
                text=label,
                anchor="w",
                fill="#B45309",
                font=("Segoe UI", 9, "bold"),
                tags=("pdf", "pdf_manual_label"),
            )

    def _on_pdf_press(self, event):
        if self._mode != "pdf":
            return None
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        page_info = self._pdf_page_at(x, y)
        if page_info is None:
            return None
        self._pdf_selection_start = (x, y, page_info)
        self.canvas.delete("pdf_selection")
        self._pdf_selection_item = self.canvas.create_rectangle(
            x,
            y,
            x,
            y,
            outline="#2563EB",
            width=2,
            dash=(4, 2),
            tags=("pdf_selection",),
        )
        return "break"

    def _on_pdf_drag(self, event):
        if self._mode != "pdf" or self._pdf_selection_start is None or self._pdf_selection_item is None:
            return None
        start_x, start_y, page_info = self._pdf_selection_start
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        x = min(max(x, page_info["x"]), page_info["x"] + page_info["image_width"])
        y = min(max(y, page_info["y"]), page_info["y"] + page_info["image_height"])
        self.canvas.coords(self._pdf_selection_item, start_x, start_y, x, y)
        return "break"

    def _on_pdf_release(self, event):
        if self._mode != "pdf" or self._pdf_selection_start is None:
            return None
        start_x, start_y, page_info = self._pdf_selection_start
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self._pdf_selection_start = None
        if self._pdf_selection_item is not None:
            self.canvas.delete(self._pdf_selection_item)
            self._pdf_selection_item = None

        x = min(max(x, page_info["x"]), page_info["x"] + page_info["image_width"])
        y = min(max(y, page_info["y"]), page_info["y"] + page_info["image_height"])
        if abs(x - start_x) < 5 and abs(y - start_y) < 5:
            block = self._pdf_block_at(page_info, x, y)
            if block is None:
                return "break"
            pdf_rect = getattr(block, "rect", (0, 0, 0, 0))
            selected_text = getattr(block, "text", "")
        else:
            pdf_rect = self._canvas_rect_to_pdf(page_info, (start_x, start_y, x, y))
            selected_text = self._text_for_pdf_rect(page_info, pdf_rect)

        if self.on_pdf_area_selected:
            self.on_pdf_area_selected(page_info["page_index"], pdf_rect, selected_text)
        return "break"

    def _pdf_page_at(self, x: float, y: float) -> dict | None:
        for page_info in self._pdf_page_items:
            if (
                page_info["x"] <= x <= page_info["x"] + page_info["image_width"]
                and page_info["y"] <= y <= page_info["y"] + page_info["image_height"]
            ):
                return page_info
        return None

    def _pdf_block_at(self, page_info: dict, x: float, y: float):
        for block in page_info.get("blocks", []):
            rect = self._pdf_rect_to_canvas(page_info, getattr(block, "rect", (0, 0, 0, 0)))
            if rect is None:
                continue
            x0, y0, x1, y1 = rect
            if x0 <= x <= x1 and y0 <= y <= y1:
                return block
        return None

    def _text_for_pdf_rect(self, page_info: dict, pdf_rect: tuple[float, float, float, float]) -> str:
        values = []
        for block in page_info.get("blocks", []):
            block_rect = getattr(block, "rect", (0, 0, 0, 0))
            if self._rects_intersect(block_rect, pdf_rect):
                values.append(getattr(block, "text", ""))
        return " ".join(" ".join(value.split()) for value in values if value).strip()

    def _canvas_rect_to_pdf(self, page_info: dict, canvas_rect: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
        x0, y0, x1, y1 = canvas_rect
        left = max(min(x0, x1), page_info["x"])
        right = min(max(x0, x1), page_info["x"] + page_info["image_width"])
        top = max(min(y0, y1), page_info["y"])
        bottom = min(max(y0, y1), page_info["y"] + page_info["image_height"])
        scale_x = page_info["pdf_width"] / max(1, page_info["image_width"])
        scale_y = page_info["pdf_height"] / max(1, page_info["image_height"])
        return (
            (left - page_info["x"]) * scale_x,
            (top - page_info["y"]) * scale_y,
            (right - page_info["x"]) * scale_x,
            (bottom - page_info["y"]) * scale_y,
        )

    def _pdf_rect_to_canvas(self, page_info: dict, pdf_rect: tuple[float, float, float, float]):
        try:
            x0, y0, x1, y1 = [float(value) for value in pdf_rect]
        except (TypeError, ValueError):
            return None
        scale_x = page_info["image_width"] / max(1.0, page_info["pdf_width"])
        scale_y = page_info["image_height"] / max(1.0, page_info["pdf_height"])
        return (
            page_info["x"] + min(x0, x1) * scale_x,
            page_info["y"] + min(y0, y1) * scale_y,
            page_info["x"] + max(x0, x1) * scale_x,
            page_info["y"] + max(y0, y1) * scale_y,
        )

    @staticmethod
    def _rects_intersect(left, right) -> bool:
        lx0, ly0, lx1, ly1 = [float(value) for value in left]
        rx0, ry0, rx1, ry1 = [float(value) for value in right]
        lx0, lx1 = min(lx0, lx1), max(lx0, lx1)
        ly0, ly1 = min(ly0, ly1), max(ly0, ly1)
        rx0, rx1 = min(rx0, rx1), max(rx0, rx1)
        ry0, ry1 = min(ry0, ry1), max(ry0, ry1)
        return not (lx1 < rx0 or rx1 < lx0 or ly1 < ry0 or ry1 < ly0)

    @staticmethod
    def _area_marker(area) -> str:
        return str(area.get("marker", "")) if isinstance(area, dict) else str(getattr(area, "marker", ""))

    @staticmethod
    def _area_page_index(area) -> int:
        return int(area.get("page_index", 0) if isinstance(area, dict) else getattr(area, "page_index", 0))

    @staticmethod
    def _area_rect(area):
        return area.get("rect", (0, 0, 0, 0)) if isinstance(area, dict) else getattr(area, "rect", (0, 0, 0, 0))

    def _marker_label(self, marker: str) -> str:
        value = self._pdf_values.get(marker, "").strip()
        label = marker.strip("{}") or "AREA"
        if value:
            clean = " ".join(value.split())
            if len(clean) > 24:
                clean = clean[:21].rstrip() + "..."
            label = f"{label}: {clean}"
        return label

    def _current_loading_symbol(self):
        available = [image for image in self._loading_symbol_images if image is not None]
        if not available:
            return None
        return available[self._loading_symbol_index % len(available)]

    def _pulse_loading_symbol(self) -> None:
        if self._loading_symbol_widget is None:
            return
        self._loading_symbol_index += 1
        image = self._current_loading_symbol()
        if image is not None:
            self._loading_symbol_widget.configure(image=image)
        self._loading_job = self.after(1000, self._pulse_loading_symbol)

    def _stop_loading(self) -> None:
        if self._loading_job is not None:
            try:
                self.after_cancel(self._loading_job)
            except Exception:
                pass
            self._loading_job = None
        if self._loading_symbol_widget is not None:
            self._loading_symbol_widget.destroy()
            self._loading_symbol_widget = None

    def _update_counts(self, content: str) -> None:
        words = len(re.findall(r"\S+", content))
        chars = len(content)
        pages = max(1, math.ceil(chars / 2600))
        self.page_label.configure(text=f"Página 1 de {pages}")
        self.words_label.configure(text=f"{words:,} palavras".replace(",", "."))
        self.chars_label.configure(text=f"{chars:,} caracteres".replace(",", "."))

    def _zoom_out(self) -> None:
        index = max(0, self.ZOOM_STEPS.index(self.zoom_percent) - 1)
        self.zoom_percent = self.ZOOM_STEPS[index]
        self._apply_zoom()

    def _zoom_in(self) -> None:
        index = min(len(self.ZOOM_STEPS) - 1, self.ZOOM_STEPS.index(self.zoom_percent) + 1)
        self.zoom_percent = self.ZOOM_STEPS[index]
        self._apply_zoom()

    def _apply_zoom(self) -> None:
        self.zoom_label.configure(text=f"{self.zoom_percent}%")
        if self._mode == "pdf":
            if self.on_refresh:
                self.on_refresh()
            return
        font_size = max(8, int(11 * self.zoom_percent / 100))
        self.text.configure(font=("Segoe UI", font_size))
        self.text.tag_configure("marker", foreground="#16A34A", background="#F0FDF4", font=("Segoe UI", font_size, "bold"))
        self.text.tag_configure("empty", foreground=COLORS["text3"], justify="center", font=("Segoe UI", max(10, font_size)))
        self._update_page_geometry()

    def _on_canvas_resize(self, _event=None) -> None:
        if self._mode == "pdf":
            self._render_pdf_canvas()
            return
        self._update_page_geometry()

    def _on_mousewheel(self, event) -> str:
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"

    def _update_page_geometry(self) -> None:
        self.update_idletasks()
        canvas_width = max(self.canvas.winfo_width(), 500)
        scale = self.zoom_percent / 100
        page_width = int(self.PAGE_BASE_WIDTH * scale)
        a4_height = int(page_width * self.PAGE_RATIO)
        page_height = max(a4_height, self._estimate_content_height(page_width))
        self.shadow.configure(width=page_width + 3, height=page_height + 3)
        self.shadow.grid_propagate(False)
        self.page.configure(width=page_width, height=page_height)
        self.page.grid_propagate(False)
        pad_x = max(24, int(self.PAGE_PADDING_X * scale))
        pad_y = max(28, int(self.PAGE_PADDING_TOP * scale))
        self.text.configure(padx=pad_x, pady=pad_y)
        top_margin = 18
        bottom_margin = 24
        self.canvas.coords(self.page_window, max(canvas_width // 2, page_width // 2 + 24), top_margin)
        self.canvas.configure(scrollregion=(0, 0, max(canvas_width, page_width + 80), page_height + top_margin + bottom_margin))

    def _estimate_content_height(self, page_width: int) -> int:
        font_size = max(8, int(11 * self.zoom_percent / 100))
        scale = self.zoom_percent / 100
        pad_x = max(24, int(self.PAGE_PADDING_X * scale))
        pad_top = max(28, int(self.PAGE_PADDING_TOP * scale))
        pad_bottom = max(48, int(self.PAGE_PADDING_BOTTOM * scale))
        usable_width = max(220, page_width - (pad_x * 2))
        chars_per_line = max(30, int(usable_width / max(5.6, font_size * 0.54)))
        lines = self._content.splitlines() or [""]
        visual_lines = sum(max(1, math.ceil(len(line) / chars_per_line)) for line in lines)
        line_height = max(16, int(font_size * 1.85))
        return pad_top + pad_bottom + visual_lines * line_height
