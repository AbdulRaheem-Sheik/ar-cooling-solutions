"""Build the static website for GitHub Pages.

Renders every public page of the Flask app to _site/<page>/index.html, copies the static
files, and adds 404.html and CNAME (the custom domain). sitemap.xml, robots.txt and
favicon.ico are fetched from the app's own routes, so they match what the live server serves.
Every internal link is checked; the build fails if any points to a missing page.

    python tools/build_static.py            # build _site/
    python tools/build_static.py --serve    # build, then preview at http://127.0.0.1:8000

The GitHub Action in .github/workflows/deploy.yml runs this on every push to main.
"""

import argparse
import http.server
import os
import re
import secrets
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "_site"
# Always published; other static files (images) only when a built page references them,
# so unused originals and spare photos never bloat the site.
# The share banner is only linked by absolute URL (og:image), so it is listed here too.
# The social post pictures are likewise only linked by absolute URL (see build_share_pages).
ALWAYS_STATIC = {Path("css"), Path("js"), Path("images/og-banner.jpg"), Path("images/social")}
# Files at the site root that the app serves itself (see the routes in app.py).
ROOT_FILES = ("sitemap.xml", "robots.txt", "favicon.ico")
SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


def load_app():
    # The live site has no logins, so the build uses a throwaway signing key.
    os.environ.setdefault("SECRET_KEY", secrets.token_hex(32))
    os.environ["AR_DEBUG"] = "0"
    os.environ["AR_STATIC_BUILD"] = "1"   # leaves out sample content (see SHOW_SAMPLE_CONTENT in app.py)
    # Build from the JSON files in data/ (what is committed), never from a local database
    # with unexported admin edits: a fresh throwaway database is filled from data/.
    os.environ["AR_DATABASE_PATH"] = str(Path(tempfile.mkdtemp(prefix="ar-build-")) / "build.db")
    sys.path.insert(0, str(ROOT))
    import app as site  # noqa: E402

    return site


def page_paths(site):
    """Every public page. The list itself lives in app.py, so the build, the site check and
    the live sitemap can never disagree about which pages exist."""
    with site.app.test_request_context():
        return site.public_page_paths()


def output_file(path):
    """Every page is a folder with index.html: /products/ -> products/index.html.
    That avoids clashes such as products.html next to the products/ folder."""
    return OUTPUT / path.strip("/") / "index.html" if path.strip("/") else OUTPUT / "index.html"


def build_share_pages(site):
    """One small page per social media post (data/social/posts.json) at /go/<id>/.
    X, Facebook and LinkedIn read its tags to show the post's picture as a link card;
    a visitor who clicks the card is sent straight on to the post's page on the site.
    The pictures are drawn by tools/make_social_posts.py; the page itself comes from
    render_share_page in app.py, which also serves it on the live server."""
    for post in site.get_social_posts():
        if not site.social_post_image_exists(post):
            sys.exit(f"Social post {post['id']}: picture {post['image']} is missing; run tools/make_social_posts.py.")
        destination = output_file(f"/go/{post['id']}/")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(site.render_share_page(post), encoding="utf-8")


def build(site):
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir()
    client = site.app.test_client()

    pages = page_paths(site)
    for path in pages:
        response = client.get(path)
        if response.status_code != 200:
            sys.exit(f"{path} returned {response.status_code}; fix it before publishing.")
        target = output_file(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(response.data)

    not_found = client.get("/this-page-does-not-exist/")
    (OUTPUT / "404.html").write_bytes(not_found.data)

    build_share_pages(site)

    referenced = set()
    for page_file in OUTPUT.rglob("*.html"):
        for url in re.findall(r'(?:href|src)="/static/([^"?#]+)', page_file.read_text(encoding="utf-8")):
            referenced.add(Path(unquote(url)))
    static_out = OUTPUT / "static"
    for source in (ROOT / "static").rglob("*"):
        relative = source.relative_to(ROOT / "static")
        if source.is_dir():
            continue
        if relative not in referenced and not any(relative.is_relative_to(folder) for folder in ALWAYS_STATIC):
            continue
        destination = static_out / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    # The same routes the live server answers, so the static copy cannot drift from it.
    for filename in ROOT_FILES:
        response = client.get(f"/{filename}")
        if response.status_code != 200:
            sys.exit(f"/{filename} returned {response.status_code}; fix it before publishing.")
        (OUTPUT / filename).write_bytes(response.data)

    (OUTPUT / "CNAME").write_text(urlsplit(site.SITE_URL).hostname + "\n", encoding="utf-8")
    (OUTPUT / ".nojekyll").write_text("", encoding="utf-8")  # serve files as-is, no Jekyll processing
    return pages


def check_links():
    """Every href/src that points inside the site must resolve to a built file."""
    broken = []
    for page_file in OUTPUT.rglob("*.html"):
        for url in re.findall(r'(?:href|src)="([^"]+)"', page_file.read_text(encoding="utf-8")):
            parts = urlsplit(url)
            if parts.scheme or parts.netloc or url.startswith(("#", "mailto:", "tel:")):
                continue
            path = unquote(parts.path)
            if not path.startswith("/"):
                continue
            if path.endswith("/"):
                ok = output_file(path).is_file()
            else:
                ok = (OUTPUT / path.lstrip("/")).is_file()  # a file such as /static/css/style.css
            if not ok:
                hint = " (page links must end with /)" if output_file(path + "/").is_file() else ""
                broken.append(f"{page_file.relative_to(OUTPUT)} -> {url}{hint}")
    if broken:
        sys.exit("Broken internal links:\n  " + "\n  ".join(sorted(set(broken))))


def check_sitemap(site):
    """Every address in sitemap.xml must be a built page, like the internal link check."""
    root = ET.parse(OUTPUT / "sitemap.xml").getroot()
    missing = []
    for loc in root.iter(f"{SITEMAP_NS}loc"):
        path = loc.text.removeprefix(site.SITE_URL)
        if not path.startswith("/") or not output_file(path).is_file():
            missing.append(loc.text)
    if missing:
        sys.exit("sitemap.xml lists pages that were not built:\n  " + "\n  ".join(missing))


class PagesLikeHandler(http.server.SimpleHTTPRequestHandler):
    """Local preview that behaves like GitHub Pages: folders serve index.html,
    /products redirects to /products/, and missing pages get 404.html."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(OUTPUT), **kwargs)

    def send_error(self, code, message=None, explain=None):
        if code != 404:
            return super().send_error(code, message, explain)
        body = (OUTPUT / "404.html").read_bytes()
        self.send_response(404)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--serve", action="store_true", help="preview the build at http://127.0.0.1:8000")
    args = parser.parse_args()

    site = load_app()
    pages = build(site)
    check_links()
    check_sitemap(site)
    files = sum(1 for f in OUTPUT.rglob("*") if f.is_file())
    size = sum(f.stat().st_size for f in OUTPUT.rglob("*") if f.is_file()) / 1024 / 1024
    print(f"Built {len(pages)} pages + 404 into {OUTPUT.name}/ ({files} files, {size:.1f} MB). All internal links and sitemap OK.")

    if args.serve:
        print("Preview: http://127.0.0.1:8000  (Ctrl+C to stop)")
        http.server.ThreadingHTTPServer(("127.0.0.1", 8000), PagesLikeHandler).serve_forever()


if __name__ == "__main__":
    main()
