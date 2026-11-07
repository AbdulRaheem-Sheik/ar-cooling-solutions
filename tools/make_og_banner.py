"""Create the 1200x630 share image shown when a page link is posted on WhatsApp, Facebook,
LinkedIn or X (the og:image / twitter:image in templates/base.html).

Writes static/images/og-banner.jpg: the AR logo and business name on white, with a maroon
panel and the services. Run it again if the logo, colours or wording change:

    pip install pillow        # only needed for this script, not for the site
    python tools/make_og_banner.py
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
LOGO = ROOT / "static" / "images" / "ar_logo.jpg"
OUTPUT = ROOT / "static" / "images" / "og-banner.jpg"
WIDTH, HEIGHT = 1200, 630
MAROON, MAROON_DARK = (0x93, 0x23, 0x40), (0x6A, 0x14, 0x28)
ACCENT = (0x7B, 0x1A, 0x30)          # --accent
GOLD = (0xD9, 0xA4, 0x41)            # --gold
INK, INK_SOFT = (0x1D, 0x1A, 0x1C), (0x57, 0x52, 0x5A)
PANEL_X = 760                        # where the maroon panel starts

# Bold and regular sans fonts: Windows first, then common Linux paths.
FONT_FILES = {
    "bold": ["C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
    "regular": ["C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
}


def font(weight, size):
    for path in FONT_FILES[weight]:
        if Path(path).is_file():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size)


def main():
    banner = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(banner)

    # Maroon panel on the right, a diagonal gradient like the site's buttons.
    for x in range(PANEL_X, WIDTH):
        t = (x - PANEL_X) / (WIDTH - PANEL_X)
        draw.line([(x, 0), (x, HEIGHT)], fill=tuple(round(a + (b - a) * t) for a, b in zip(MAROON, MAROON_DARK)))
    draw.rectangle([PANEL_X, 0, PANEL_X + 6, HEIGHT], fill=GOLD)

    logo = Image.open(LOGO).convert("RGB")
    logo.thumbnail((150, 150), Image.LANCZOS)
    banner.paste(logo, (80, 92))

    draw.text((80, 270), "AR Cooling Solutions", font=font("bold", 58), fill=ACCENT)
    draw.rectangle([80, 352, 160, 357], fill=GOLD)
    draw.text((80, 380), "AC & HVAC sales, service", font=font("regular", 32), fill=INK)
    draw.text((80, 422), "and genuine spare parts in Hyderabad", font=font("regular", 32), fill=INK)
    draw.text((80, 520), "arcooling.in  ·  +91 88013 81405", font=font("bold", 24), fill=INK_SOFT)

    items = ["Installation", "Repairs", "AMC & maintenance", "Gas refilling", "Spare parts", "Commercial HVAC"]
    for index, item in enumerate(items):
        y = 150 + index * 58
        draw.ellipse([PANEL_X + 66, y + 12, PANEL_X + 78, y + 24], fill=GOLD)
        draw.text((PANEL_X + 96, y), item, font=font("bold", 28), fill="white")

    banner.save(OUTPUT, "JPEG", quality=88, optimize=True, progressive=True)
    print(f"Wrote {OUTPUT.relative_to(ROOT).as_posix()} ({OUTPUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
