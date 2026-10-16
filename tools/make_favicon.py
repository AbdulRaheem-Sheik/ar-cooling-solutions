"""Create the site icons from the logo: a white snowflake on the maroon tile used in the header.

Writes static/favicon.ico (16/32/48 px, browser tabs) and static/apple-touch-icon.png
(180 px, phone home screens). Run it again if the logo or brand colour changes:

    pip install pillow        # only needed for this script, not for the site
    python tools/make_favicon.py
"""

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
LOGO = ROOT / "static" / "images" / "Cooling-Logo-PNG-Photo.png"
STATIC = ROOT / "static"
TOP, BOTTOM = (0x93, 0x23, 0x40), (0x6A, 0x14, 0x28)   # --maroon-600 to the header's darker end
SIZE = 512                                              # drawn large, then scaled down cleanly


def gradient_tile(radius_ratio):
    """Diagonal maroon gradient, like the header's brand mark, with rounded corners."""
    tile = Image.new("RGB", (SIZE, SIZE))
    pixels = tile.load()
    for y in range(SIZE):
        for x in range(SIZE):
            t = (x + y) / (2 * (SIZE - 1))
            pixels[x, y] = tuple(round(a + (b - a) * t) for a, b in zip(TOP, BOTTOM))
    if not radius_ratio:
        return tile.convert("RGBA")
    mask = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, SIZE - 1, SIZE - 1), radius=round(SIZE * radius_ratio), fill=255)
    tile = tile.convert("RGBA")
    tile.putalpha(mask)
    return tile


def white_snowflake(scale):
    logo = Image.open(LOGO).convert("RGBA")
    logo = logo.crop(logo.getchannel("A").getbbox())
    white = Image.new("RGBA", logo.size, (255, 255, 255, 255))
    white.putalpha(logo.getchannel("A"))
    side = round(SIZE * scale)
    white.thumbnail((side, side), Image.LANCZOS)
    return white


def compose(radius_ratio, scale):
    tile = gradient_tile(radius_ratio)
    flake = white_snowflake(scale)
    tile.alpha_composite(flake, ((SIZE - flake.width) // 2, (SIZE - flake.height) // 2))
    return tile


def main():
    # Browser tabs: rounded tile like the header mark, snowflake large enough to read at 16 px.
    compose(radius_ratio=0.22, scale=0.72).save(STATIC / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    # Phones round the corners themselves, so the touch icon is a full square with more padding.
    compose(radius_ratio=0, scale=0.62).convert("RGB").resize((180, 180), Image.LANCZOS).save(
        STATIC / "apple-touch-icon.png", optimize=True
    )
    for name in ("favicon.ico", "apple-touch-icon.png"):
        print(f"static/{name}: {(STATIC / name).stat().st_size // 1024 or 1} KB")


if __name__ == "__main__":
    main()
