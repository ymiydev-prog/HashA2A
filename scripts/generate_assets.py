"""Generate favicon.png and og-image.png for HashA2A brand assets."""
import math
from PIL import Image, ImageDraw, ImageFont

# Brand colors
BLUE = (59, 130, 246)
PURPLE = (139, 92, 246)
BG = (6, 8, 15)
WHITE = (240, 242, 247)
MUTED = (139, 146, 168)

STATIC = __import__("pathlib").Path(__file__).resolve().parent.parent / "static"


def _gradient(draw, x1, y1, x2, y2, c1, c2, steps=128):
    for i in range(steps):
        t = i / (steps - 1)
        r = int(c1[0] + (c2[0] - c1[0]) * t)
        g = int(c1[1] + (c2[1] - c1[1]) * t)
        b = int(c1[2] + (c2[2] - c1[2]) * t)
        dy = y1 + (y2 - y1) * t
        draw.line([(x1, dy), (x2, dy)], fill=(r, g, b), width=int((y2 - y1) / steps) + 1)


def _rounded_rect(draw, xy, r, fill, width=0, outline=None):
    """Draw a rounded rectangle."""
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=r, fill=fill, width=width, outline=outline)


def draw_diamond_mark(draw, cx, cy, size):
    """Draw the brand diamond mark at center (cx, cy) with given size."""
    half = size / 2
    r = size * 0.18  # corner radius proportional

    # The diamond is a square rotated 45 degrees
    # We draw it with Pillow by drawing a diamond shape (not a rotated rect)
    # Points of a diamond: top, right, bottom, left
    top = (cx, cy - half)
    right = (cx + half, cy)
    bottom = (cx, cy + half)
    left = (cx - half, cy)

    # Draw gradient fill
    # We'll approximate by drawing the gradient vertically within the diamond
    # Create a square mask
    mask_size = int(size * 1.5)
    mask = Image.new("L", (mask_size, mask_size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.polygon([top, right, bottom, left], fill=255)

    # Create gradient image the same size
    grad = Image.new("RGBA", (mask_size, mask_size), (0, 0, 0, 0))
    grad_draw = ImageDraw.Draw(grad)
    # Draw vertical gradient
    for i in range(mask_size):
        t = i / (mask_size - 1)
        r_val = int(BLUE[0] + (PURPLE[0] - BLUE[0]) * t)
        g_val = int(BLUE[1] + (PURPLE[1] - BLUE[1]) * t)
        b_val = int(BLUE[2] + (PURPLE[2] - BLUE[2]) * t)
        grad_draw.line([(0, i), (mask_size - 1, i)], fill=(r_val, g_val, b_val))

    # Composite using mask
    offset = (cx - half, cy - half)  # not exact for diamond but close enough
    # Better: paste centered
    px = int(cx - mask_size / 2)
    py = int(cy - mask_size / 2)
    draw.bitmap((px, py), mask, fill=BLUE)  # fallback

    # Simple approach: draw a diamond with solid gradient approximation
    # Actually let me just use a simpler approach
    # Draw the diamond as filled polygon with best effort color
    # We'll do a two-tone diamond: top half blue, bottom half purple
    # Midpoint
    mid = (cx, cy)
    # Upper triangle (blue)
    draw.polygon([top, right, mid], fill=BLUE)
    draw.polygon([top, left, mid], fill=BLUE)
    # Lower triangle (purple)
    draw.polygon([bottom, right, mid], fill=PURPLE)
    draw.polygon([bottom, left, mid], fill=PURPLE)

    # Highlight border (thin)
    draw.polygon([top, right, bottom, left], outline=WHITE, width=2)


def _find_font(size, bold=False):
    """Try to find a good font."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/TTF/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()


def generate_favicon():
    """Generate 64x64 favicon PNG."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw_diamond_mark(draw, size // 2, size // 2, size * 0.75)
    path = STATIC / "favicon.png"
    img.save(path, "PNG")
    print(f"  ✓ favicon.png  ({path.stat().st_size / 1024:.1f} KB)")


def generate_og_image():
    """Generate 1200x630 Open Graph image."""
    w, h = 1200, 630
    img = Image.new("RGBA", (w, h), BG)
    draw = ImageDraw.Draw(img)

    # Subtle grid pattern
    for x in range(0, w, 40):
        draw.line([(x, 0), (x, h)], fill=(255, 255, 255, 2))
    for y in range(0, h, 40):
        draw.line([(0, y), (w, y)], fill=(255, 255, 255, 2))

    # Gradient overlay
    for i in range(h):
        t = 1 - i / h
        r = int(BG[0] + (BLUE[0] - BG[0]) * t * 0.08)
        g = int(BG[1] + (BLUE[1] - BG[1]) * t * 0.08)
        b = int(BG[2] + (BLUE[2] - BG[2]) * t * 0.08)
        draw.line([(0, i), (w, i)], fill=(r, g, b))

    # Diamond mark (center-left)
    diamond_size = 180
    draw_diamond_mark(draw, 300, h // 2, diamond_size)

    # "HashA2A" text
    font_large = _find_font(72, bold=True)
    font_small = _find_font(26, bold=False)

    text_x = 420
    text_y = h // 2 - 50
    draw.text((text_x, text_y), "Hash", fill=BLUE, font=font_large)
    w1 = draw.textbbox((0, 0), "Hash", font=font_large)[2]
    draw.text((text_x + w1, text_y), "A2A", fill=PURPLE, font=font_large)

    # Tagline
    tagline = "Agent-to-Agent Intelligence Layer on Hedera"
    draw.text((text_x, text_y + 90), tagline, fill=MUTED, font=font_small)

    # Decorative line
    line_y = text_y + 78
    for i in range(120):
        t = i / 119
        r = int(BLUE[0] + (PURPLE[0] - BLUE[0]) * t)
        g = int(BLUE[1] + (PURPLE[1] - BLUE[1]) * t)
        b = int(BLUE[2] + (PURPLE[2] - BLUE[2]) * t)
        draw.line([(text_x + i, line_y), (text_x + i, line_y + 3)], fill=(r, g, b))

    path = STATIC / "og-image.png"
    img.save(path, "PNG")
    print(f"  ✓ og-image.png  ({path.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    STATIC.mkdir(parents=True, exist_ok=True)
    print("Generating HashA2A brand assets...")
    generate_favicon()
    generate_og_image()
    print("Done!")
