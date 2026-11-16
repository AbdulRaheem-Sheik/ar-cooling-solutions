"""Automated check of the whole website. Run before every pull request.

    .venv/Scripts/python tools/check_site.py          # local checks (a few seconds + the build)
    .venv/Scripts/python tools/check_site.py --live   # also check https://arcooling.in

Local checks use a throwaway database and a test admin login, so your real data, .env and
admin password are never touched:
  - every public page renders (200, with a <title>); unknown pages give 404
  - every social share page (/go/<id>/) renders and its picture exists
  - admin: locked when logged out, login with the security token works, a wrong password
    and a form without the token are refused, the dashboard and an edit page open
  - the static build (tools/build_static.py) succeeds and its internal link check passes
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
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIVE_URL = "https://arcooling.in"

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


def check_static_build():
    print("Static build (GitHub Pages)")
    result = subprocess.run([sys.executable, str(ROOT / "tools" / "build_static.py")],
                            capture_output=True, text=True, cwd=ROOT)
    last_line = (result.stdout.strip().splitlines() or [""])[-1]
    check(result.returncode == 0, "build and internal link check", (result.stderr or result.stdout).strip()[-300:])
    if result.returncode == 0:
        print(f"        {last_line}")


def check_live(site):
    print(f"Live site ({LIVE_URL})")
    paths = ["/", "/services/", "/products/", "/parts/", "/parts/compressors/", "/enquiry/", "/admin/login",
             "/sitemap.xml", "/robots.txt"]
    paths += [f"/go/{p['id']}/" for p in site.get_social_posts()]
    bad = []
    for path in paths:
        try:
            with urllib.request.urlopen(urllib.request.Request(LIVE_URL + path, headers={"User-Agent": "ar-check"}),
                                        timeout=20) as response:
                if response.status != 200:
                    bad.append(f"{path} -> {response.status}")
        except urllib.error.HTTPError as error:
            # sitemap/robots exist only in the static build; the live app may not serve them
            if path not in ("/sitemap.xml", "/robots.txt"):
                bad.append(f"{path} -> {error.code}")
            else:
                print(f"  NOTE  {path} -> {error.code} on the live server")
        except Exception as error:  # certificate, DNS or connection problems
            bad.append(f"{path} -> {error}")
    check(not bad, f"{len(paths)} live pages over HTTPS", "; ".join(bad[:5]))


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--live", action="store_true", help=f"also check {LIVE_URL}")
    parser.add_argument("--skip-build", action="store_true", help="skip the static build (faster)")
    args = parser.parse_args()

    site, build_static = load_app()
    with site.app.test_request_context():
        check_pages(site, build_static)
    check_admin(site)
    if not args.skip_build:
        check_static_build()
    if args.live:
        check_live(site)

    print(f"\n{'ALL CHECKS PASSED' if not failures else f'{len(failures)} CHECK(S) FAILED: ' + '; '.join(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
