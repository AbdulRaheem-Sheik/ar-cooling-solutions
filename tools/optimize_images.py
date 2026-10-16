"""Shrink product and service photos for fast page loads.

Photos larger than MAX_SIDE pixels are scaled down, and every JPEG is re-saved as an
optimised progressive JPEG without camera metadata (EXIF, including GPS location).
A file is only replaced when the result is smaller. Originals stay in git history.

Run it after adding or replacing photos:

    pip install pillow        # only needed for this script, not for the site
    python tools/optimize_images.py
"""

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
FOLDERS = [ROOT / "static" / "images" / "products", ROOT / "static" / "images" / "services"]
MAX_SIDE = 1600      # sharp on large and high-resolution screens; cards show ~400 px
QUALITY = 82         # visually identical to the original for photos
WARN_PNG_KB = 300    # large PNG photos should be converted to JPEG (and the data file updated)


def optimise(path):
    original_size = path.stat().st_size
    image = ImageOps.exif_transpose(Image.open(path))  # keep phone photos the right way up
    if path.suffix.lower() == ".png":
        if original_size > WARN_PNG_KB * 1024:
            print(f"  note: {path.name} is a {original_size // 1024} KB PNG; a JPEG copy would be much smaller")
        return
    if max(image.size) > MAX_SIDE:
        image.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
    buffer = BytesIO()
    image.convert("RGB").save(buffer, "JPEG", quality=QUALITY, optimize=True, progressive=True)
    if buffer.tell() < original_size:
        path.write_bytes(buffer.getvalue())
        print(f"  {path.name}: {original_size // 1024} KB -> {buffer.tell() // 1024} KB  ({image.width}x{image.height})")
    else:
        print(f"  {path.name}: already optimised ({original_size // 1024} KB)")


def main():
    for folder in FOLDERS:
        print(folder.relative_to(ROOT).as_posix())
        for path in sorted(folder.iterdir()):
            if path.suffix.lower() in {".jpg", ".jpeg", ".png"}:
                optimise(path)


if __name__ == "__main__":
    main()
