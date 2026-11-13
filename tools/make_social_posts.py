"""Draw the images for the daily social media posts.

Reads data/social/posts.json and, for every post whose images are missing, draws
  static/images/social/<image>          1200x630 share card (X, Facebook, LinkedIn link preview)
  static/images/social/square/<image>   1080x1080 picture (Instagram)
from one of the site's own photos, in the site's maroon and gold colours.

    pip install playwright      (uses the installed Chrome: set CHROME=/path/to/chrome if needed)
    python tools/make_social_posts.py

tools/build_static.py then publishes a small page per post at /go/<id>/ that carries the
share card and sends visitors on to the post's page on the site.
"""

import asyncio
import html
import json
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IMAGES = ROOT / "static" / "images"
OUT = IMAGES / "social"
POSTS = ROOT / "data" / "social" / "posts.json"

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Inter',sans-serif;background:#fff;overflow:hidden;position:relative}
.photo{position:absolute;background-color:#fff;background-repeat:no-repeat}
.tag{position:absolute;background:#fff;color:#7b1a30;font-family:'Poppins';font-weight:600;letter-spacing:.14em;
     text-transform:uppercase;border-radius:999px;box-shadow:0 6px 20px rgba(29,26,28,.18)}
.panel{position:absolute;background:linear-gradient(135deg,#932340 0%,#5a0f20 100%);color:#fff}
h1{font-family:'Poppins';font-weight:700;letter-spacing:-.01em}
h1 em{font-style:normal;color:#e8c27a}
ul{list-style:none}
li{font-weight:500;position:relative;color:#fbeef1}
li:before{content:'';position:absolute;left:0;border-radius:50%;background:#c9973f}
.foot{position:absolute;background:#fff;display:flex;align-items:center;justify-content:space-between}
.brand{display:flex;align-items:center}
.brand b{font-family:'Poppins';font-weight:700;color:#1d1a1c;line-height:1.15;display:block}
.brand span{display:block;font-weight:500;color:#57525a}
.cta{text-align:right}
.cta .url{font-family:'Poppins';font-weight:700;color:#7b1a30}
.cta .ph{font-weight:600;color:#57525a}
"""
SQUARE = """
body{width:1080px;height:1080px}
.photo{inset:0 0 auto 0;height:590px}
.tag{top:44px;left:48px;font-size:24px;padding:12px 22px}
.panel{left:0;right:0;top:560px;bottom:0;border-radius:44px 44px 0 0;padding:50px 56px 0}
h1{font-size:60px;line-height:1.12;margin-bottom:26px}
li{font-size:30px;line-height:1.3;padding-left:44px;margin-bottom:14px}
li:before{top:9px;width:22px;height:22px;box-shadow:inset 0 0 0 6px #c9973f,inset 0 0 0 11px #5a0f20}
.foot{left:0;right:0;bottom:0;height:120px;padding:0 56px}
.brand{gap:20px}.brand img{height:58px}.brand b{font-size:27px}.brand span{font-size:19px}
.cta .url{font-size:34px}.cta .ph{font-size:22px;margin-top:2px}
"""
CARD = """
body{width:1200px;height:630px}
.photo{left:0;top:0;width:520px;height:630px}
.tag{top:30px;left:30px;font-size:19px;padding:9px 18px}
.panel{left:490px;right:0;top:0;bottom:0;border-radius:40px 0 0 40px;padding:46px 44px 0 50px}
h1{font-size:45px;line-height:1.14;margin-bottom:22px}
li{font-size:24px;line-height:1.3;padding-left:36px;margin-bottom:11px}
li:before{top:7px;width:18px;height:18px;box-shadow:inset 0 0 0 5px #c9973f,inset 0 0 0 9px #5a0f20}
.foot{left:490px;right:0;bottom:0;height:104px;padding:0 40px 0 50px;border-radius:0 0 0 40px}
.brand{gap:14px}.brand img{height:44px}.brand b{font-size:20px}.brand span{font-size:15px}
.cta .url{font-size:28px}.cta .ph{font-size:16px;margin-top:2px}
"""


def page(post, layout):
    bullets = "".join(f"<li>{html.escape(b)}</li>" for b in post["bullets"])
    lead, _, accent = post["headline"].partition("|")
    headline = html.escape(lead) + (f"<em>{html.escape(accent)}</em>" if accent else "")
    photo = (IMAGES / post["photo"]).as_uri()
    fit = post.get("photo_fit", "cover")
    position = post.get("photo_position", "center")
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS}{layout}
.photo{{background-image:url('{photo}');background-size:{fit};background-position:{position}}}</style></head><body>
<div class="photo"></div><div class="tag">{html.escape(post["tag"])}</div>
<div class="panel"><h1>{headline}</h1><ul>{bullets}</ul></div>
<div class="foot"><div class="brand"><img src="{(IMAGES / 'ar_logo.jpg').as_uri()}"><div><b>AR Cooling Solutions</b><span>Hyderabad's cooling specialists</span></div></div>
<div class="cta"><div class="url">arcooling.in</div><div class="ph">Call / WhatsApp +91 88013 81405</div></div></div>
</body></html>"""


async def main():
    from playwright.async_api import async_playwright

    posts = json.loads(POSTS.read_text(encoding="utf-8"))
    todo = [p for p in posts if not (OUT / p["image"]).is_file() or not (OUT / "square" / p["image"]).is_file()]
    if not todo:
        print("Nothing to draw: every post already has its images.")
        return
    (OUT / "square").mkdir(parents=True, exist_ok=True)
    chrome = os.environ.get("CHROME") or shutil.which("google-chrome") or shutil.which("chromium")
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=chrome, args=["--no-sandbox", "--allow-file-access-from-files"])
        for post in todo:
            for layout, size, target in ((CARD, (1200, 630), OUT / post["image"]),
                                         (SQUARE, (1080, 1080), OUT / "square" / post["image"])):
                tab = await browser.new_page(viewport={"width": size[0], "height": size[1]})
                scratch = OUT / "_draft.html"
                scratch.write_text(page(post, layout), encoding="utf-8")
                await tab.goto(scratch.as_uri())
                await tab.wait_for_timeout(400)
                await tab.screenshot(path=str(target), type="jpeg", quality=88)
                await tab.close()
                scratch.unlink()
            print("drew", post["image"])
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
