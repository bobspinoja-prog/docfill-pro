COLORS = {
    "bg": "#07130D",
    "bg2": "#0B1F16",
    "bg3": "#10291D",
    "bg4": "#132F22",
    "border": "#1E3D2C",
    "border2": "#244B36",
    "border3": "#315A43",
    "green": "#22C55E",
    "green2": "#16A34A",
    "green3": "#4ADE80",
    "green4": "#86EFAC",
    "text": "#F8FAFC",
    "text2": "#CBD5E1",
    "text3": "#94A3B8",
    "input": "#07130D",
    "red": "#EF4444",
}

FONT_FAMILY = "Inter"
FONT_FALLBACK = "Segoe UI"


def font(size: int, weight: str | None = None) -> tuple:
    if weight:
        return (FONT_FAMILY, size, weight)
    return (FONT_FAMILY, size)


def symbol_font(size: int, weight: str | None = None) -> tuple:
    if weight:
        return ("Segoe UI Symbol", size, weight)
    return ("Segoe UI Symbol", size)


FIELD_STYLE = {
    "fg_color": COLORS["input"],
    "border_color": COLORS["border3"],
    "border_width": 1,
    "text_color": COLORS["text"],
    "placeholder_text_color": COLORS["text3"],
    "corner_radius": 5,
    "height": 30,
    "font": font(11),
}

CARD_STYLE = {
    "fg_color": COLORS["bg3"],
    "corner_radius": 8,
    "border_width": 1,
    "border_color": COLORS["border2"],
}
