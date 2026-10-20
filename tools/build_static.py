"""Build the static website for GitHub Pages.

Renders every public page of the Flask app to _site/<page>/index.html, copies the static
files, and adds 404.html, sitemap.xml, robots.txt and CNAME (the custom domain).
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
from datetime import date
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "_site"
# Always published; other static files (images) only when a built page references them,
# so unused originals and spare photos never bloat the site.
ALWAYS_STATIC = {Path("css"), Path("js")}
# Pages that should not be listed for search engines.
NOT_IN_SITEMAP = {"/enquiry/thank-you/"}


def load_app():
    # The live site has no logins, so the build uses a throwaway signing key.
    os.environ.setdefault("SECRET_KEY", secrets.token_hex(32))
    os.environ["AR_DEBUG"] = "0"
    sys.path.insert(0, str(ROOT))
    import app as site  # noqa: E402

    return site


def page_paths(site):
    with site.app.test_request_context():
        paths = [site.url_for(endpoint) for endpoint in
                 ("home", "products", "services", "spare_parts", "about", "product_enquiry", "enquiry_thanks", "privacy")]
        paths += [site.url_for("product_detail", slug=p["slug"]) for p in site.get_product_types()]
        paths += [site.url_for("service_detail", slug=s["slug"]) for s in site.get_services()]
    return paths


def output_file(path):
    """Every page is a folder with index.html: /products/ -> products/index.html.
    That avoids clashes such as products.html next to the products/ folder."""
    return OUTPUT / path.strip("/") / "index.html" if path.strip("/") else OUTPUT / "index.html"


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

    referenced = set()
    for html in OUTPUT.rglob("*.html"):
        for url in re.findall(r'(?:href|src)="/static/([^"?#]+)', html.read_text(encoding="utf-8")):
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

    # Some browsers and tools ask for /favicon.ico without reading the page's <link> tags.
    shutil.copy2(ROOT / "static" / "favicon.ico", OUTPUT / "favicon.ico")

    site_url = site.SITE_URL
    today = date.today().isoformat()
    urls = "".join(
        f"  <url><loc>{site_url}{p}</loc><lastmod>{today}</lastmod></url>\n"
        for p in pages if p not in NOT_IN_SITEMAP
    )
    (OUTPUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + "</urlset>\n",
        encoding="utf-8",
    )
    (OUTPUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {site_url}/sitemap.xml\n", encoding="utf-8")
    (OUTPUT / "CNAME").write_text(urlsplit(site_url).hostname + "\n", encoding="utf-8")
    (OUTPUT / ".nojekyll").write_text("", encoding="utf-8")  # serve files as-is, no Jekyll processing
    return pages


def check_links():
    """Every href/src that points inside the site must resolve to a built file."""
    broken = []
    for html in OUTPUT.rglob("*.html"):
        for url in re.findall(r'(?:href|src)="([^"]+)"', html.read_text(encoding="utf-8")):
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
                broken.append(f"{html.relative_to(OUTPUT)} -> {url}{hint}")
    if broken:
        sys.exit("Broken internal links:\n  " + "\n  ".join(sorted(set(broken))))


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
    files = sum(1 for f in OUTPUT.rglob("*") if f.is_file())
    size = sum(f.stat().st_size for f in OUTPUT.rglob("*") if f.is_file()) / 1024 / 1024
    print(f"Built {len(pages)} pages + 404 into {OUTPUT.name}/ ({files} files, {size:.1f} MB). All internal links OK.")

    if args.serve:
        print("Preview: http://127.0.0.1:8000  (Ctrl+C to stop)")
        http.server.ThreadingHTTPServer(("127.0.0.1", 8000), PagesLikeHandler).serve_forever()


if __name__ == "__main__":
    main()
