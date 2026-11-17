#!/usr/bin/env python3
"""Composite Gemini Plus promo UI panels onto the cinematic banner background.

Produces three 2048x768 variants with identical content on left AND right edges.
Characters/faces/background are never regenerated — only overlay compositing.
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
REPO_ASSETS = ROOT / "assets"
CURSOR_ASSETS = Path("/home/ubuntu/.cursor/projects/agent-repos-PlayerokPic/assets")
ASSETS = REPO_ASSETS if (REPO_ASSETS / "482d734d-b898-4393-938a-2738ce51b526.jpg").exists() else CURSOR_ASSETS
BG_PATH = ASSETS / "482d734d-b898-4393-938a-2738ce51b526.jpg"
OUT_DIR = ROOT / "banners"
ARTIFACTS = Path("/opt/cursor/artifacts")

W, H = 2048, 768

FONT_BOLD = "/usr/share/fonts/truetype/macos/Inter-Bold.ttf"
FONT_SEMI = "/usr/share/fonts/truetype/macos/Inter-SemiBold.ttf"
FONT_MED = "/usr/share/fonts/truetype/macos/Inter-Medium.ttf"

GEMINI_COLORS = {
    "G": (66, 133, 244),
    "e": (234, 67, 53),
    "m": (251, 188, 5),
    "i": (66, 133, 244),
    "n": (52, 168, 83),
    "i2": (234, 67, 53),
}

BLUE_BTN = (66, 133, 244, 255)


def cover_fit(img: Image.Image, tw: int, th: int) -> Image.Image:
    """Scale to cover target, center-crop. Preserves photoreal content."""
    sw, sh = img.size
    scale = max(tw / sw, th / sh)
    nw, nh = int(round(sw * scale)), int(round(sh * scale))
    resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - tw) // 2
    top = (nh - th) // 2
    return resized.crop((left, top, left + tw, top + th))


def rounded_rect(
    size: tuple[int, int],
    radius: int,
    fill: tuple[int, ...],
    border: tuple[int, ...] | None = None,
    border_width: int = 1,
) -> Image.Image:
    w, h = size
    # Draw at 2x for smoother corners then downscale
    scale = 2
    img = Image.new("RGBA", (w * scale, h * scale), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    r = radius * scale
    bw = border_width * scale
    bbox = [0, 0, w * scale - 1, h * scale - 1]
    if border:
        draw.rounded_rectangle(bbox, radius=r, fill=border)
        inner = [bw, bw, w * scale - 1 - bw, h * scale - 1 - bw]
        draw.rounded_rectangle(inner, radius=max(0, r - bw), fill=fill)
    else:
        draw.rounded_rectangle(bbox, radius=r, fill=fill)
    return img.resize(size, Image.Resampling.LANCZOS)


def draw_sparkle(size: int = 28) -> Image.Image:
    """Four-pointed sparkle with orange→blue gradient."""
    s = size * 4
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx = cy = s / 2
    # Outer diamond points (4-point star)
    outer = s * 0.48
    inner = s * 0.14

    def pt(ang: float, rad: float) -> tuple[float, float]:
        return (cx + rad * math.cos(ang), cy + rad * math.sin(ang))

    # Points at 45° offsets for diamond sparkle (pointy up)
    angles = [-math.pi / 2, -math.pi / 4, 0, math.pi / 4, math.pi / 2, 3 * math.pi / 4, math.pi, -3 * math.pi / 4]
    pts = []
    for i, a in enumerate(angles):
        rad = outer if i % 2 == 0 else inner
        pts.append(pt(a, rad))

    # Gradient fill via mask + colored layers
    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).polygon(pts, fill=255)

    grad = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    for y in range(s):
        t = y / max(1, s - 1)
        # orange (top-left bias) -> blue (bottom-right)
        r = int(255 * (1 - t) + 66 * t)
        g = int(140 * (1 - t) + 133 * t)
        b = int(40 * (1 - t) + 244 * t)
        gd.line([(0, y), (s, y)], fill=(r, g, b, 255))

    # Horizontal orange tint on left
    for x in range(s):
        t = x / max(1, s - 1)
        overlay = Image.new("RGBA", (1, s), (255, int(120 + 40 * (1 - t)), 40, int(80 * (1 - t))))
        grad.paste(overlay, (x, 0), overlay)

    out = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    out.paste(grad, (0, 0), mask)
    # Soft glow
    glow = out.filter(ImageFilter.GaussianBlur(radius=s * 0.04))
    combined = Image.alpha_composite(glow, out)
    return combined.resize((size, size), Image.Resampling.LANCZOS)


def draw_calendar_icon(size: int = 26) -> Image.Image:
    s = size * 3
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    stroke = max(2, s // 14)
    pad = s // 8
    # Outer rounded rect
    d.rounded_rectangle(
        [pad, pad + s // 10, s - pad, s - pad],
        radius=s // 8,
        outline=(255, 255, 255, 230),
        width=stroke,
    )
    # Top bar
    y1 = pad + s // 5
    d.line([(pad + stroke, y1), (s - pad - stroke, y1)], fill=(255, 255, 255, 230), width=stroke)
    # Hangers
    hx1, hx2 = pad + s // 4, s - pad - s // 4
    d.line([(hx1, pad // 2), (hx1, pad + s // 8)], fill=(255, 255, 255, 230), width=stroke)
    d.line([(hx2, pad // 2), (hx2, pad + s // 8)], fill=(255, 255, 255, 230), width=stroke)
    # Dots (days)
    grid_y0 = y1 + s // 8
    for row in range(2):
        for col in range(3):
            x = pad + s // 5 + col * (s // 4)
            y = grid_y0 + row * (s // 5)
            r = max(2, s // 22)
            d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, 220))
    return img.resize((size, size), Image.Resampling.LANCZOS)


def text_size(font: ImageFont.FreeTypeFont, text: str) -> tuple[int, int]:
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def draw_gemini_plus(draw: ImageDraw.ImageDraw, cx: int, cy: int, font: ImageFont.FreeTypeFont) -> None:
    gemini = "Gemini"
    plus = " Plus"
    colors = [
        GEMINI_COLORS["G"],
        GEMINI_COLORS["e"],
        GEMINI_COLORS["m"],
        GEMINI_COLORS["i"],
        GEMINI_COLORS["n"],
        GEMINI_COLORS["i2"],
    ]
    # Measure total width
    total_w = sum(text_size(font, ch)[0] for ch in gemini) + text_size(font, plus)[0]
    x = cx - total_w // 2
    # Vertical center using capital letter metrics
    sample_h = text_size(font, "G")[1]
    y = cy - sample_h // 2 - font.getbbox("G")[1]
    for ch, color in zip(gemini, colors):
        draw.text((x, y), ch, font=font, fill=color + (255,))
        x += text_size(font, ch)[0]
    draw.text((x, y), plus, font=font, fill=(255, 255, 255, 255))


def build_panel_stack(cfg: dict) -> Image.Image:
    """Build one vertical UI stack as a transparent RGBA image."""
    col_w = cfg["col_w"]
    gap = cfg["gap"]
    radius = cfg["radius"]
    fill = cfg["panel_fill"]  # RGBA
    border = cfg["panel_border"]
    border_w = cfg["border_w"]
    pad_x = cfg["pad_x"]
    row_h = cfg["row_h"]
    half_h = cfg["half_h"]
    btn_h = cfg["btn_h"]
    title_size = cfg["title_size"]
    body_size = cfg["body_size"]
    btn_size = cfg["btn_size"]
    icon_sz = cfg["icon_sz"]
    cal_sz = cfg["cal_sz"]
    blur_backdrop = cfg.get("blur_backdrop", 0)

    sparkle = draw_sparkle(icon_sz)
    calendar = draw_calendar_icon(cal_sz)

    font_title = ImageFont.truetype(FONT_BOLD, title_size)
    font_body = ImageFont.truetype(FONT_SEMI, body_size)
    font_btn = ImageFont.truetype(FONT_BOLD, btn_size)

    total_h = row_h + gap + half_h + gap + row_h + gap + btn_h
    stack = Image.new("RGBA", (col_w, total_h), (0, 0, 0, 0))
    y = 0

    # Optional frosted backdrop under whole stack
    if blur_backdrop > 0:
        frost = rounded_rect(
            (col_w, total_h),
            radius + 8,
            (20, 20, 24, cfg.get("frost_alpha", 60)),
            border=(255, 255, 255, 25),
            border_width=1,
        )
        frost = frost.filter(ImageFilter.GaussianBlur(radius=1))
        stack.alpha_composite(frost, (0, 0))

    # 1) Gemini Plus
    panel = rounded_rect((col_w, row_h), radius, fill, border, border_w)
    stack.alpha_composite(panel, (0, y))
    layer = Image.new("RGBA", (col_w, row_h), (0, 0, 0, 0))
    draw_gemini_plus(ImageDraw.Draw(layer), col_w // 2, row_h // 2, font_title)
    stack.alpha_composite(layer, (0, y))
    y += row_h + gap

    # 2) Two half panels
    half_w = (col_w - gap) // 2
    for i, label in enumerate(["Nano Banana Pro", "Veo 3.1"]):
        x = i * (half_w + gap)
        panel = rounded_rect((half_w, half_h), radius, fill, border, border_w)
        stack.alpha_composite(panel, (x, y))
        # icon + text
        content = Image.new("RGBA", (half_w, half_h), (0, 0, 0, 0))
        cd = ImageDraw.Draw(content)
        tw, th = text_size(font_body, label)
        # Fit: shrink font if needed
        f = font_body
        fs = body_size
        while tw + icon_sz + 10 > half_w - pad_x * 2 and fs > 10:
            fs -= 1
            f = ImageFont.truetype(FONT_SEMI, fs)
            tw, th = text_size(f, label)
        content_w = icon_sz + 8 + tw
        sx = (half_w - content_w) // 2
        sy = (half_h - icon_sz) // 2
        content.alpha_composite(sparkle, (sx, sy))
        ty = (half_h - th) // 2 - f.getbbox(label)[1]
        cd.text((sx + icon_sz + 8, ty), label, font=f, fill=(255, 255, 255, 255))
        stack.alpha_composite(content, (x, y))
    y += half_h + gap

    # 3) Calendar row
    panel = rounded_rect((col_w, row_h), radius, fill, border, border_w)
    stack.alpha_composite(panel, (0, y))
    content = Image.new("RGBA", (col_w, row_h), (0, 0, 0, 0))
    cd = ImageDraw.Draw(content)
    label = "6 месяцев"
    tw, th = text_size(font_body, label)
    content_w = cal_sz + 10 + tw
    sx = (col_w - content_w) // 2
    sy = (row_h - cal_sz) // 2
    content.alpha_composite(calendar, (sx, sy))
    ty = (row_h - th) // 2 - font_body.getbbox(label)[1]
    cd.text((sx + cal_sz + 10, ty), label, font=font_body, fill=(255, 255, 255, 255))
    stack.alpha_composite(content, (0, y))
    y += row_h + gap

    # 4) Blue pill button
    btn = rounded_rect((col_w, btn_h), btn_h // 2, BLUE_BTN, None, 0)
    # Soft shadow under button
    shadow = Image.new("RGBA", (col_w + 8, btn_h + 8), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle([4, 4, col_w + 3, btn_h + 3], radius=btn_h // 2, fill=(0, 0, 0, 90))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=4))
    stack.alpha_composite(shadow, (-4, y - 2))
    stack.alpha_composite(btn, (0, y))
    content = Image.new("RGBA", (col_w, btn_h), (0, 0, 0, 0))
    cd = ImageDraw.Draw(content)
    label = "Всего за 169₽"
    tw, th = text_size(font_btn, label)
    tx = (col_w - tw) // 2
    ty = (btn_h - th) // 2 - font_btn.getbbox(label)[1]
    cd.text((tx, ty), label, font=font_btn, fill=(255, 255, 255, 255))
    stack.alpha_composite(content, (0, y))

    # Optional outer shadow on whole stack
    if cfg.get("stack_shadow"):
        sh = Image.new("RGBA", (col_w + 20, total_h + 20), (0, 0, 0, 0))
        mask = Image.new("L", (col_w, total_h), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, col_w - 1, total_h - 1], radius=radius, fill=cfg.get("shadow_alpha", 100))
        black = Image.new("RGBA", (col_w, total_h), (0, 0, 0, 255))
        sh.paste(black, (10, 10), mask)
        sh = sh.filter(ImageFilter.GaussianBlur(radius=cfg.get("shadow_blur", 8)))
        out = Image.new("RGBA", (col_w + 20, total_h + 20), (0, 0, 0, 0))
        out.alpha_composite(sh, (0, 0))
        out.alpha_composite(stack, (10, 10))
        return out

    return stack


def place_stacks(bg: Image.Image, stack: Image.Image, margin_x: int, margin_y: int | None) -> Image.Image:
    """Paste stack on far left and far right; vertically centered if margin_y is None."""
    out = bg.convert("RGBA")
    sh = stack.height
    sw = stack.width
    if margin_y is None:
        y = (H - sh) // 2
    else:
        y = margin_y

    # Left
    out.alpha_composite(stack, (margin_x, y))
    # Right — mirror x from right edge
    rx = W - margin_x - sw
    out.alpha_composite(stack, (rx, y))
    return out.convert("RGB")


VARIANTS = {
    "v1": {
        # Closely matching reference scale/spacing/opacity
        "col_w": 340,
        "gap": 10,
        "radius": 14,
        "panel_fill": (32, 32, 36, 165),
        "panel_border": (255, 255, 255, 55),
        "border_w": 1,
        "pad_x": 12,
        "row_h": 56,
        "half_h": 48,
        "btn_h": 52,
        "title_size": 28,
        "body_size": 15,
        "btn_size": 20,
        "icon_sz": 22,
        "cal_sz": 24,
        "margin_x": 28,
        "margin_y": None,
        "stack_shadow": False,
        "blur_backdrop": 0,
    },
    "v2": {
        # Slightly larger panels, more edge padding, lower vertical position
        "col_w": 390,
        "gap": 12,
        "radius": 16,
        "panel_fill": (28, 28, 32, 175),
        "panel_border": (255, 255, 255, 60),
        "border_w": 1,
        "pad_x": 14,
        "row_h": 64,
        "half_h": 54,
        "btn_h": 58,
        "title_size": 32,
        "body_size": 16,
        "btn_size": 22,
        "icon_sz": 24,
        "cal_sz": 26,
        "margin_x": 40,
        "margin_y": 90,  # a bit lower / more top padding
        "stack_shadow": False,
        "blur_backdrop": 0,
    },
    "v3": {
        # Different glass opacity / blur / shadow; tighter column
        "col_w": 310,
        "gap": 8,
        "radius": 12,
        "panel_fill": (18, 18, 22, 130),
        "panel_border": (255, 255, 255, 70),
        "border_w": 1,
        "pad_x": 10,
        "row_h": 52,
        "half_h": 44,
        "btn_h": 48,
        "title_size": 26,
        "body_size": 13,
        "btn_size": 18,
        "icon_sz": 20,
        "cal_sz": 22,
        "margin_x": 22,
        "margin_y": None,
        "stack_shadow": True,
        "shadow_alpha": 120,
        "shadow_blur": 10,
        "blur_backdrop": 1,
        "frost_alpha": 70,
    },
}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)

    bg = Image.open(BG_PATH).convert("RGB")
    canvas = cover_fit(bg, W, H)
    assert canvas.size == (W, H), canvas.size

    for name, cfg in VARIANTS.items():
        stack = build_panel_stack(cfg)
        # If stack has shadow padding, adjust margins
        margin_x = cfg["margin_x"]
        if cfg.get("stack_shadow"):
            # stack is larger by 20px; content offset 10 — keep visual edge margin
            margin_x = max(8, margin_x - 10)
        banner = place_stacks(canvas, stack, margin_x, cfg["margin_y"])
        assert banner.size == (W, H)

        out_name = f"gemini-plus-banner-{name}.png"
        out_path = OUT_DIR / out_name
        banner.save(out_path, "PNG", optimize=True)
        art_path = ARTIFACTS / out_name
        banner.save(art_path, "PNG", optimize=True)
        print(f"Wrote {out_path} and {art_path} size={banner.size}")


if __name__ == "__main__":
    main()
