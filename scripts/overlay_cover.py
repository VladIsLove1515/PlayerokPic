#!/usr/bin/env python3
"""Накладывает русский текст лота на левую пустую зону обложки."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "images" / "steam_kz_cover_base.jpg"
OUT_PNG = ROOT / "outputs" / "steam_kz_cover.png"
OUT_JPG = ROOT / "outputs" / "steam_kz_cover.jpg"
FONT_BLACK = ROOT / "fonts" / "Montserrat-Black.ttf"
FONT_EXTRABOLD = ROOT / "fonts" / "Montserrat-ExtraBold.ttf"
FONT_BOLD = ROOT / "fonts" / "Montserrat-Bold.ttf"

STEAM_CYAN = (102, 192, 244)
KZ_TEAL = (0, 175, 202)
KZ_GOLD = (254, 197, 12)
WHITE = (255, 255, 255)
NAVY = (8, 18, 36)


def load_font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size=size)


def fit_font(path: Path, text: str, max_width: int, start: int, min_size: int = 28) -> ImageFont.FreeTypeFont:
    size = start
    dummy = ImageDraw.Draw(Image.new("RGB", (4, 4)))
    while size >= min_size:
        font = load_font(path, size)
        if dummy.textbbox((0, 0), text, font=font)[2] <= max_width:
            return font
        size -= 2
    return load_font(path, min_size)


def text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, stroke: int = 0) -> tuple[int, int]:
    x0, y0, x1, y1 = draw.textbbox((0, 0), text, font=font, stroke_width=stroke)
    return x1 - x0, y1 - y0


def draw_text(
    base: Image.Image,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int],
    stroke_fill: tuple[int, int, int],
    stroke: int,
    shadow: int = 10,
) -> None:
    x, y = xy
    shadow_layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)
    shadow_draw.text(
        (x + 4, y + 6),
        text,
        font=font,
        fill=(0, 0, 0, 170),
        stroke_width=stroke + 2,
        stroke_fill=(0, 0, 0, 170),
    )
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=shadow))
    base.alpha_composite(shadow_layer)
    draw = ImageDraw.Draw(base)
    draw.text(
        (x, y),
        text,
        font=font,
        fill=fill + ((255,)),
        stroke_width=stroke,
        stroke_fill=stroke_fill + ((255,)),
    )


def draw_badge(
    base: Image.Image,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    width: int,
) -> int:
    draw = ImageDraw.Draw(base)
    tw, th = text_size(draw, text, font)
    pad_x, pad_y = 28, 14
    bw = max(width, tw + pad_x * 2)
    bh = th + pad_y * 2
    x, y = xy
    radius = bh // 2
    badge = Image.new("RGBA", base.size, (0, 0, 0, 0))
    badge_draw = ImageDraw.Draw(badge)
    rect = (x, y, x + bw, y + bh)
    badge_draw.rounded_rectangle(rect, radius=radius, fill=KZ_GOLD + (235,))
    inner = (x + 4, y + 4, x + bw - 4, y + bh - 4)
    badge_draw.rounded_rectangle(inner, radius=radius - 3, fill=NAVY + (235,))
    base.alpha_composite(badge)
    tx = x + (bw - tw) // 2
    ty = y + (bh - th) // 2 - 2
    ImageDraw.Draw(base).text((tx, ty), text, font=font, fill=WHITE + (255,))
    return bh


def main() -> None:
    src = Image.open(SRC).convert("RGBA")
    w, h = src.size
    col_left = int(w * 0.06)
    col_width = int(w * 0.42)

    kicker_font = fit_font(FONT_EXTRABOLD, "АККАУНТ", col_width, 54)
    title_font = fit_font(FONT_BLACK, "STEAM", col_width, 132)
    region_font = fit_font(FONT_EXTRABOLD, "КАЗАХСТАН", col_width, 58)
    badge_font = fit_font(FONT_BOLD, "АВТОВЫДАЧА", col_width - 20, 36)

    probe = ImageDraw.Draw(src)
    kicker_w, kicker_h = text_size(probe, "АККАУНТ", kicker_font, stroke=4)
    title_w, title_h = text_size(probe, "STEAM", title_font, stroke=8)
    region_w, region_h = text_size(probe, "КАЗАХСТАН", region_font, stroke=5)

    gap_small, gap_mid, gap_line = 8, 18, 22
    badge_h = 64
    block_h = kicker_h + gap_small + title_h + gap_small + region_h + gap_line + 6 + gap_mid + badge_h
    y = int(h * 0.22)
    if y + block_h > h * 0.82:
        y = int((h - block_h) / 2)

    draw_text(src, (col_left, y), "АККАУНТ", kicker_font, KZ_GOLD, NAVY, stroke=4, shadow=8)
    y += kicker_h + gap_small
    draw_text(src, (col_left, y), "STEAM", title_font, WHITE, (10, 70, 110), stroke=8, shadow=12)
    y += title_h + gap_small
    draw_text(src, (col_left, y), "КАЗАХСТАН", region_font, KZ_TEAL, NAVY, stroke=5, shadow=8)
    y += region_h + gap_line

    line = Image.new("RGBA", src.size, (0, 0, 0, 0))
    line_draw = ImageDraw.Draw(line)
    line_w = max(kicker_w, title_w, region_w)
    line_draw.rectangle((col_left, y, col_left + min(line_w, col_width), y + 5), fill=KZ_GOLD + (230,))
    src.alpha_composite(line)
    y += 6 + gap_mid

    draw_badge(src, (col_left, y), "АВТОВЫДАЧА", badge_font, min(line_w, col_width))

    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    rgb = Image.new("RGB", src.size, NAVY)
    rgb.paste(src, mask=src.split()[-1])
    rgb.save(OUT_PNG, "PNG", optimize=True)
    rgb.save(OUT_JPG, "JPEG", quality=94, subsampling=1)
    print(f"wrote {OUT_PNG} and {OUT_JPG} ({w}x{h})")


if __name__ == "__main__":
    main()
