"""Prepare client and partner logos for the website.

For every logo this script removes the solid background, trims the empty
margins, and centres the result on an identical transparent canvas, scaled so
that wide wordmarks and square marks look equally big. Originals are left
untouched; output goes to static/images/logos/<group>/<name>.png.

Run it again after adding or replacing a logo:

    pip install pillow        # only needed for this script, not for the site
    python tools/process_logos.py
"""

from math import sqrt
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SOURCES = {
    "partners": ROOT / "static" / "images" / "brand_logos",
    "clients": ROOT / "static" / "images" / "clients",
}
OUTPUT = ROOT / "static" / "images" / "logos"

CANVAS = (480, 180)        # every output image has this size (shown at 160 x 60)
MAX_BOX = (440, 150)       # largest the logo itself may get inside the canvas
TARGET_AREA = 0.30         # share of the canvas a logo should cover, for equal visual weight
ALPHA_FLOOR = 0.05         # fainter pixels than this are treated as background noise

# Logos with a thin frame drawn around the edge: pixels to crop before processing.
EDGE_CROP = {"mandev.jpg": 8, "biophore.jpg": 8}
# Logos on a dark background whose white parts must stay visible on a white page.
RECOLOR_LIGHT = {"vguard.png": (64, 56, 60)}
# Logos on a patterned background that is part of the brand: kept as a tile.
KEEP_BACKGROUND = {"wow_momo.jpg"}


def pixel_data(image):
    """All pixels as tuples (Pillow 12+ renamed getdata to get_flattened_data)."""
    getter = getattr(image, "get_flattened_data", None) or image.getdata
    return getter()


def remove_background(image, crop=0):
    """Turn the background colour (taken from the corner) into transparency."""
    image = image.convert("RGBA")
    if crop:
        image = image.crop((crop, crop, image.width - crop, image.height - crop))
    bg = image.getpixel((1, 1))[:3]
    dark_bg = sum(bg) / 3 < 80
    pixels = []
    for r, g, b, a in pixel_data(image):
        if dark_bg:
            # Unmix against black: alpha comes from the brightest channel.
            alpha = max(r, g, b) / 255
            rgb = (r, g, b) if alpha == 0 else tuple(min(255, round(c / alpha)) for c in (r, g, b))
        else:
            # Bring a near-white background up to pure white, then unmix against white.
            r, g, b = (min(255, round(c * 255 / max(bc, 1))) for c, bc in zip((r, g, b), bg))
            alpha = max(255 - r, 255 - g, 255 - b) / 255
            rgb = (255, 255, 255) if alpha == 0 else tuple(
                max(0, round(255 - (255 - c) / alpha)) for c in (r, g, b)
            )
        alpha *= a / 255
        if alpha < ALPHA_FLOOR:
            pixels.append((0, 0, 0, 0))
        else:
            pixels.append((*rgb, round(alpha * 255)))
    image.putdata(pixels)
    return image


def recolor_light(image, color):
    """Paint near-white, unsaturated pixels in `color` (e.g. white text from a dark logo)."""
    pixels = []
    for r, g, b, a in pixel_data(image):
        if a and min(r, g, b) > 170 and max(r, g, b) - min(r, g, b) < 45:
            pixels.append((*color, a))
        else:
            pixels.append((r, g, b, a))
    image.putdata(pixels)
    return image


def fit_to_canvas(image):
    """Trim to content, scale to equal visual weight, and centre on the shared canvas."""
    box = image.getchannel("A").point(lambda v: 255 if v > 30 else 0).getbbox()
    if box:
        image = image.crop(box)
    ratio = image.width / image.height
    area = CANVAS[0] * CANVAS[1] * TARGET_AREA
    width, height = sqrt(area * ratio), sqrt(area / ratio)
    shrink = min(1, MAX_BOX[0] / width, MAX_BOX[1] / height)
    size = (max(1, round(width * shrink)), max(1, round(height * shrink)))
    image = image.resize(size, Image.LANCZOS)
    canvas = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    canvas.paste(image, ((CANVAS[0] - size[0]) // 2, (CANVAS[1] - size[1]) // 2), image)
    return canvas


def main():
    for group, folder in SOURCES.items():
        out_dir = OUTPUT / group
        out_dir.mkdir(parents=True, exist_ok=True)
        for path in sorted(folder.iterdir()):
            if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
                continue
            if path.name in KEEP_BACKGROUND:
                image = Image.open(path).convert("RGBA")
            else:
                image = remove_background(Image.open(path), EDGE_CROP.get(path.name, 0))
            if path.name in RECOLOR_LIGHT:
                image = recolor_light(image, RECOLOR_LIGHT[path.name])
            target = out_dir / f"{path.stem}.png"
            fit_to_canvas(image).save(target, optimize=True)
            print(f"{group}/{target.name}")


if __name__ == "__main__":
    main()
