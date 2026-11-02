#!/usr/bin/env python3
"""Накладывает русский текст на обложку лота."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = Path(__file__).resolve().parents[1]
SRC = BASE / "images" / "tiktok_1000_podpischikov_base.jpg"
OUT = BASE / "outputs" / "tiktok_1000_podpischikov_cover.jpg"
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def draw_glow_text(base: Image.Image, text: str, xy: tuple[int, int], font: ImageFont.FreeTypeFont,
                   fill=(255, 255, 255, 255), glow_colors=((0, 200, 255), (255, 40, 200)),
                   outline=10, glow_radius=18) -> None:
    """Рисует текст с неоновой обводкой и свечением."""
    x, y = xy
    # Glow layer
    glow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    for color in glow_colors:
        gdraw.text((x, y), text, font=font, fill=(*color, 210))
    glow = glow.filter(ImageFilter.GaussianBlur(glow_radius))
    base.alpha_composite(glow)

    # Hard outline
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    for dx in range(-outline, outline + 1):
        for dy in range(-outline, outline + 1):
            if dx * dx + dy * dy <= outline * outline:
                # alternate cyan / magenta outline
                color = glow_colors[0] if (dx + dy) % 2 == 0 else glow_colors[1]
                draw.text((x + dx, y + dy), text, font=font, fill=(*color, 255))
    draw.text((x, y), text, font=font, fill=fill)
    base.alpha_composite(layer)


def draw_badge(base: Image.Image, text: str, xy: tuple[int, int], font: ImageFont.FreeTypeFont) -> None:
    """Маленький бейдж +1000 как на референсе."""
    draw = ImageDraw.Draw(base)
    pad_x, pad_y = 22, 12
    bbox = font.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    # person icon circle + text width
    icon_r = th // 2 + 4
    w = pad_x * 2 + icon_r * 2 + 10 + tw
    h = pad_y * 2 + th
    x, y = xy
    # pill
    draw.rounded_rectangle((x, y, x + w, y + h), radius=h // 2, fill=(10, 10, 18, 230))
    # person icon (simple)
    cx = x + pad_x + icon_r
    cy = y + h // 2
    draw.ellipse((cx - icon_r // 2, cy - icon_r, cx + icon_r // 2, cy - icon_r // 4), fill=(240, 240, 255, 255))
    draw.ellipse((cx - icon_r + 2, cy - icon_r // 6, cx + icon_r - 2, cy + icon_r - 2), fill=(240, 240, 255, 255))
    # text
    draw.text((cx + icon_r + 8, y + pad_y - 2), text, font=font, fill=(255, 255, 255, 255))


def main() -> None:
    img = Image.open(SRC).convert("RGBA")
    w, h = img.size

    title_font = ImageFont.truetype(FONT_PATH, size=max(64, w // 11))
    word_font = ImageFont.truetype(FONT_PATH, size=max(52, w // 14))
    badge_font = ImageFont.truetype(FONT_PATH, size=max(28, w // 28))

    # Основной текст слева-по центру, как на референсе
    line1 = "+1000"
    line2 = "ПОДПИСЧИКОВ"

    # Центрируем блок по левой половине
    l1 = title_font.getbbox(line1)
    l2 = word_font.getbbox(line2)
    block_w = max(l1[2] - l1[0], l2[2] - l2[0])
    left_zone_center = int(w * 0.32)
    x1 = left_zone_center - (l1[2] - l1[0]) // 2
    x2 = left_zone_center - (l2[2] - l2[0]) // 2
    y1 = int(h * 0.28)
    y2 = y1 + (l1[3] - l1[1]) + int(h * 0.02)

    draw_glow_text(img, line1, (x1, y1), title_font, outline=max(8, w // 120), glow_radius=max(12, w // 80))
    draw_glow_text(img, line2, (x2, y2), word_font, outline=max(7, w // 140), glow_radius=max(10, w // 90))

    draw_badge(img, "+1000", (int(w * 0.04), int(h * 0.06)), badge_font)

    out = img.convert("RGB")
    out.save(OUT, quality=95)
    print(f"Saved: {OUT} ({out.size[0]}x{out.size[1]})")


if __name__ == "__main__":
    main()
