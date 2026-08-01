"""Genera el ícono de la app (PNG maestro 1024x1024) con Pillow.

Uso: python assets/icon/generate_icon.py
Produce assets/icon/AppIcon-1024.png, insumo para construir el .iconset/.icns
(ver assets/icon/build_icns.sh).
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

SIZE = 1024
OUT = Path(__file__).parent / "AppIcon-1024.png"

# Fondo: cuadrado redondeado (squircle) con degradado azul-verde,
# siguiendo el padding habitual de iconos macOS (~apx 10% de margen).
COLOR_TOP = (46, 110, 140)      # #2E6E8C
COLOR_BOTTOM = (20, 60, 82)     # #143C52
COLOR_GLYPH = (250, 250, 248)   # blanco cálido
COLOR_DOOR = (30, 78, 104)      # hueco de la puerta, mismo tono que el fondo


def _rounded_square_mask(size: int, radius: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), (size - 1, size - 1)], radius=radius, fill=255)
    return mask


def _gradient_background(size: int) -> Image.Image:
    bg = Image.new("RGB", (size, size))
    for y in range(size):
        t = y / (size - 1)
        r = round(COLOR_TOP[0] + (COLOR_BOTTOM[0] - COLOR_TOP[0]) * t)
        g = round(COLOR_TOP[1] + (COLOR_BOTTOM[1] - COLOR_TOP[1]) * t)
        b = round(COLOR_TOP[2] + (COLOR_BOTTOM[2] - COLOR_TOP[2]) * t)
        for x in range(size):
            bg.putpixel((x, y), (r, g, b))
    return bg


def build() -> None:
    margin = int(SIZE * 0.06)
    canvas_size = SIZE - 2 * margin
    radius = int(canvas_size * 0.22)

    background = _gradient_background(canvas_size)
    mask = _rounded_square_mask(canvas_size, radius)

    icon = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    icon.paste(background, (margin, margin), mask)

    draw = ImageDraw.Draw(icon)

    # Glifo: una casa simple (techo triangular + cuerpo), centrada.
    cx = SIZE / 2
    house_w = canvas_size * 0.50
    house_h = canvas_size * 0.46
    body_top = SIZE / 2 - house_h * 0.18
    body_bottom = body_top + house_h * 0.62
    left = cx - house_w / 2
    right = cx + house_w / 2
    roof_tip_y = body_top - house_h * 0.50
    eave_overhang = house_w * 0.12

    # Cuerpo de la casa
    draw.rectangle([left, body_top, right, body_bottom], fill=COLOR_GLYPH)

    # Techo (triangulo con aleros)
    draw.polygon(
        [
            (left - eave_overhang, body_top),
            (cx, roof_tip_y),
            (right + eave_overhang, body_top),
        ],
        fill=COLOR_GLYPH,
    )

    # Puerta
    door_w = house_w * 0.22
    door_h = (body_bottom - body_top) * 0.62
    door_left = cx - door_w / 2
    draw.rounded_rectangle(
        [door_left, body_bottom - door_h, door_left + door_w, body_bottom],
        radius=door_w * 0.18,
        fill=COLOR_DOOR,
    )

    icon.save(OUT)
    print(f"Ícono maestro escrito en {OUT}")


if __name__ == "__main__":
    build()
