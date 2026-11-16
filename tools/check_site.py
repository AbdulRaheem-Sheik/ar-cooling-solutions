"""Automated check of the whole website. Run before every pull request.

    .venv/Scripts/python tools/check_site.py          # local checks (a few seconds + the build)
    .venv/Scripts/python tools/check_site.py --live   # also check https://arcooling.in

Local checks use a throwaway database and a test admin login, so your real data, .env and
admin password are never touched:
  - every public page renders (200, with a <title>); unknown pages give 404
  - every social share page (/go/<id>/) renders and its picture exists
  - admin: locked when logged out, login with the security token works, a wrong password
    and a form without the token are refused, the dashboard and an edit page open
  - sitemap.xml lists exactly the public pages (no admin, share or thank-you pages), each
    one opens; robots.txt has the expected text; /favicon.ico is the site icon
  - the static build (tools/build_static.py) succeeds, its internal link and sitemap checks
    pass, and its sitemap.xml and robots.txt match what the app serves
With --live, the same files and every page in the live sitemap are fetched from the live
site (or from --live-url); a missing file is a failure.
Exits with status 1 if anything fails.
"""

import argparse
import os
import re
import secrets
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIVE_URL = "https://arcooling.in"
SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
# Written out here rather than imported from app.py, so the check is an independent
# statement of what robots.txt must say (a mistake there can hide the whole site).
ROBOTS_TEMPLATE = "User-agent: *\nAllow: /\nDisallow: /admin\n\nSitemap: {site}/sitemap.xml\n"
FORBIDDEN_IN_SITEMAP = ("/admin", "/go/", "/enquiry/thank-you/")

failures = []


def check(ok, label, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{f'  ({detail})' if detail and not ok else ''}")
    if not ok:
        failures.append(label)


def load_app():
    """Import the app with a throwaway database and test login (set before import)."""
    temp = Path(tempfile.mkdtemp(prefix="ar-check-"))
    os.environ.update({
        "AR_DATABASE_PATH": str(temp / "check.db"),
        "SECRET_KEY": secrets.token_hex(32),
        "AR_ADMIN_USERNAME": "check-admin",
        "AR_ADMIN_PASSWORD": secrets.token_urlsafe(16),
        "AR_DEBUG": "0",
    })
    os.environ.pop("AR_BEHIND_PROXY", None)   # HTTPS-only cookies would block the test login
    os.environ.pop("AR_STATIC_BUILD", None)
    sys.path[:0] = [str(ROOT), str(ROOT / "tools")]
    import app as site  # noqa: E402
    import build_static  # noqa: E402

    return site, build_static


def csrf_token(html):
    match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
    return match.group(1) if match else ""


def check_pages(site, build_static):
    print("Public pages")
    client = site.app.test_client()
    paths = build_static.page_paths(site)
    bad = []
    for path in paths:
        response = client.get(path)
        if response.status_code != 200 or b"<title>" not in response.data:
            bad.append(f"{path} -> {response.status_code}")
    check(not bad, f"{len(paths)} pages render", "; ".join(bad[:5]))
    check(client.get("/this-page-does-not-exist/").status_code == 404, "unknown page gives 404")

    print("Social share pages")
    posts = site.get_social_posts()
    bad = [p["id"] for p in posts
           if client.get(f"/go/{p['id']}/").status_code != 200 or not site.social_post_image_exists(p)]
    check(not bad, f"{len(posts)} share pages and pictures", ", ".join(bad))
    check(client.get("/go/no-such-post/").status_code == 404, "unknown share page gives 404")


def sitemap_entries(xml_bytes):
    """(loc, lastmod) pairs from a sitemap, or None if it is not a valid sitemap."""
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return None
    if root.tag != f"{SITEMAP_NS}urlset":
        return None
    return [(url.findtext(f"{SITEMAP_NS}loc", ""), url.findtext(f"{SITEMAP_NS}lastmod", ""))
            for url in root.iter(f"{SITEMAP_NS}url")]


def bad_locs(locs, site_url):
    """Sitemap addresses that are not full page addresses, or that must never be listed."""
    return [loc for loc in locs
            if not loc.startswith(site_url + "/") or not loc.endswith("/")
            or any(part in loc for part in FORBIDDEN_IN_SITEMAP)]


def favicon_bytes():
    return (ROOT / "static" / "favicon.ico").read_bytes()


def check_seo_files(site, build_static):
    """sitemap.xml, robots.txt and favicon.ico as the app serves them (also on the live server)."""
    print("Sitemap, robots.txt, favicon")
    client = site.app.test_client()

    response = client.get("/sitemap.xml")
    check(response.status_code == 200 and "xml" in response.content_type, "sitemap.xml is served as XML",
          f"{response.status_code} {response.content_type}")
    entries = sitemap_entries(response.data)
    check(entries is not None, "sitemap.xml is a valid sitemap (urlset)")
    entries = entries or []
    locs = [loc for loc, _ in entries]
    paths = [loc.removeprefix(site.SITE_URL) for loc in locs]
    expected = set(build_static.page_paths(site)) - site.NOT_IN_SITEMAP
    check(len(paths) == len(set(paths)), "no page listed twice")
    missing, extra = sorted(expected - set(paths)), sorted(set(paths) - expected)
    check(not missing and not extra, f"sitemap lists the {len(expected)} public pages",
          f"missing {missing[:3]}, extra {extra[:3]}")
    bad = bad_locs(locs, site.SITE_URL)
    check(not bad, "addresses are full, end with /, no admin, share or thank-you pages", "; ".join(bad[:5]))
    not_ok = [f"{p} -> {code}" for p in paths if (code := client.get(p).status_code) != 200]
    check(not not_ok, "every page in the sitemap opens", "; ".join(not_ok[:5]))
    today = date.today().isoformat()
    bad_dates = sorted({lastmod for _, lastmod in entries
                        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", lastmod) or lastmod != today})
    check(entries and not bad_dates, "every lastmod is today's date (YYYY-MM-DD)", ", ".join(bad_dates[:3]))

    response = client.get("/robots.txt")
    expected_robots = ROBOTS_TEMPLATE.format(site=site.SITE_URL)
    check(response.status_code == 200 and response.content_type.startswith("text/plain")
          and response.get_data(as_text=True) == expected_robots,
          "robots.txt has the expected text", f"{response.status_code} {response.content_type}")

    response = client.get("/favicon.ico")
    check(response.status_code == 200 and response.content_type.startswith("image/")
          and response.data == favicon_bytes(),
          "/favicon.ico is the site icon", f"{response.status_code} {response.content_type}")


def check_admin(site):
    print("Admin")
    client = site.app.test_client()
    username, password = os.environ["AR_ADMIN_USERNAME"], os.environ["AR_ADMIN_PASSWORD"]
    response = client.get("/admin")
    check(response.status_code == 302 and "/admin/login" in response.location, "dashboard locked when logged out")

    token = csrf_token(client.get("/admin/login").get_data(as_text=True))
    check(bool(token), "login form has a security token")
    response = client.post("/admin/login", data={"csrf_token": token, "username": username, "password": "wrong-password-1"})
    check(response.status_code == 401, "wrong password refused", str(response.status_code))
    response = client.post("/admin/login", data={"username": username, "password": password})
    check(response.status_code == 400, "login without token refused", str(response.status_code))
    response = client.post("/admin/login", data={"csrf_token": token, "username": username, "password": password})
    check(response.status_code == 302 and response.location.endswith("/admin"), "correct login works", str(response.status_code))

    dashboard = client.get("/admin")
    check(dashboard.status_code == 200 and b'class="edit"' in dashboard.data, "dashboard opens with edit links")
    edit_link = re.search(r'href="(/admin/[^"]+/edit)"', dashboard.get_data(as_text=True))
    if edit_link:
        check(client.get(edit_link.group(1)).status_code == 200, f"edit page opens ({edit_link.group(1)})")
        response = client.post(edit_link.group(1), data={"json_data": "{}"})
        check(response.status_code == 400, "save without token refused", str(response.status_code))


def check_static_build(site):
    print("Static build (GitHub Pages)")
    result = subprocess.run([sys.executable, str(ROOT / "tools" / "build_static.py")],
                            capture_output=True, text=True, cwd=ROOT)
    last_line = (result.stdout.strip().splitlines() or [""])[-1]
    check(result.returncode == 0, "build, internal link and sitemap check", (result.stderr or result.stdout).strip()[-300:])
    if result.returncode != 0:
        return
    print(f"        {last_line}")
    # Both use a fresh database filled from data/, so the page lists must be the same.
    # Only addresses are compared, not lastmod, so a run across midnight cannot fail.
    built_robots = (ROOT / "_site" / "robots.txt").read_bytes().decode("utf-8")
    check(built_robots == ROBOTS_TEMPLATE.format(site=site.SITE_URL), "built robots.txt matches the app")
    built = sitemap_entries((ROOT / "_site" / "sitemap.xml").read_bytes()) or []
    served = sitemap_entries(site.app.test_client().get("/sitemap.xml").data) or []
    check(built and {loc for loc, _ in built} == {loc for loc, _ in served},
          f"built sitemap.xml lists the same {len(built)} pages as the app")


def fetch(url):
    """GET a URL: (status, content type, body, final URL after redirects).
    Certificate, DNS or connection problems raise."""
    request = urllib.request.Request(url, headers={"User-Agent": "ar-check"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, response.headers.get("Content-Type", ""), response.read(), response.geturl()
    except urllib.error.HTTPError as error:
        return error.code, error.headers.get("Content-Type", ""), b"", error.geturl()


def check_live(site, base_url):
    """Pages and files on the live server. base_url is where to ask (normally the live
    site); the addresses inside sitemap.xml and robots.txt must always be LIVE_URL.
    The live page list is not compared with data/: admin edits make it differ on purpose."""
    print(f"Live site ({base_url})")
    paths = ["/", "/services/", "/products/", "/parts/", "/parts/compressors/", "/enquiry/", "/admin/login",
             "/sitemap.xml", "/robots.txt", "/favicon.ico"]
    paths += [f"/go/{p['id']}/" for p in site.get_social_posts()]
    bad, files = [], {}
    for path in paths:
        try:
            status, content_type, body, _ = fetch(base_url + path)
        except Exception as error:
            bad.append(f"{path} -> {error}")
            continue
        if status != 200:
            bad.append(f"{path} -> {status}")
        else:
            files[path] = (content_type, body)
    check(not bad, f"{len(paths)} live pages and files", "; ".join(bad[:5]))

    content_type, body = files.get("/robots.txt", ("", b""))
    check(content_type.startswith("text/plain") and body.decode("utf-8", "replace") == ROBOTS_TEMPLATE.format(site=LIVE_URL),
          "live robots.txt has the expected text")

    content_type, body = files.get("/sitemap.xml", ("", b""))
    entries = sitemap_entries(body) or []
    check("xml" in content_type and bool(entries), f"live sitemap.xml is a valid sitemap ({len(entries)} pages)")
    if entries:
        locs = [loc for loc, _ in entries]
        bad = bad_locs(locs, LIVE_URL)
        check(not bad, "live sitemap addresses are full, end with /, no admin, share or thank-you pages",
              "; ".join(bad[:5]))
        not_ok = []
        for loc in locs:   # one after the other, so the small server is never rushed
            path = loc.removeprefix(LIVE_URL)
            try:
                status = fetch(base_url + path)[0]
            except Exception as error:
                status = error
            if status != 200:
                not_ok.append(f"{path} -> {status}")
        check(not not_ok, f"all {len(locs)} live sitemap pages open", "; ".join(not_ok[:5]))

    content_type, body = files.get("/favicon.ico", ("", b""))
    check(content_type.startswith("image/") and body == favicon_bytes(), "live /favicon.ico is the site icon")

    if base_url == LIVE_URL:
        try:
            status, _, _, final_url = fetch("https://www.arcooling.in/robots.txt")
        except Exception as error:
            status, final_url = error, ""
        check(status == 200 and final_url == LIVE_URL + "/robots.txt",
              "www.arcooling.in redirects to the main address", f"{status} {final_url}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--live", action="store_true", help=f"also check {LIVE_URL}")
    parser.add_argument("--live-url", default=LIVE_URL, metavar="URL",
                        help="where the live check asks (e.g. http://127.0.0.1:8080 to try it on a local serve.py)")
    parser.add_argument("--skip-build", action="store_true", help="skip the static build (faster)")
    args = parser.parse_args()

    site, build_static = load_app()
    with site.app.test_request_context():
        check_pages(site, build_static)
        check_seo_files(site, build_static)
    check_admin(site)
    if not args.skip_build:
        check_static_build(site)
    if args.live:
        check_live(site, args.live_url.rstrip("/"))

    print(f"\n{'ALL CHECKS PASSED' if not failures else f'{len(failures)} CHECK(S) FAILED: ' + '; '.join(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
