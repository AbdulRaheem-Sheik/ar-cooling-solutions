# Review: Serve sitemap.xml, robots.txt and favicon.ico on the live site — APPROVE

Reviewed: `git diff feature/website-team...fix/live-sitemap-robots` (commits `641b4bd`, `74d59d2`),
against 01 (incl. Owner decisions), 02 (incl. Coordinator decisions), 03 and 04 (PASS).

## Summary
The change does what was asked and nothing more. Three small GET routes were added to `app.py`
(`/sitemap.xml`, `/robots.txt`, `/favicon.ico`). The page list moved from `build_static.py` into
`public_page_paths()` in `app.py`, and the static build now fetches the three files from those
same routes, so the live and static copies run the same code. `check_site.py` gained solid local,
build and live checks: a missing live file is now a FAIL. It also has a `--live-url` option, which
made the negative test (AC10) possible.

The code follows the design closely and matches the existing style (`render_share_page`
pattern, small functions, comments that say why). Slugs are XML-escaped. No new packages. No
template, `store.py`, `deploy/` or `data/` changes.

Files in the branch's commits: `app.py`, `tools/build_static.py`, `tools/check_site.py` and
the three task docs (01–03). The owner's uncommitted edits in
`data/products/05-package-ac-units.json` and `data/products/08-vrv-vrf-units.json` are **not**
in any commit on this branch (confirmed with `git log --name-only feature/website-team..fix/live-sitemap-robots`).
`04-test-report.md` is uncommitted, which is expected; the deployer commits it.

Security: the new routes are public, read-only GETs, so CSRF does not apply. No admin path
changed. There are no secrets or personal data in the diff and no new external scripts. The
favicon is served with `send_from_directory` and a fixed filename, so no path comes from the user.

Live-site safety: no existing URL changed. `/go/<id>/` is untouched. Caddy already proxies every
path to the app (`deploy/oracle/Caddyfile`), so no server config is needed. A sitemap request
costs a few SQLite reads, which is fine on the 1 GB server. The static build still passes, per the
tester's run.

## Findings
1. [nit] `app.py` `public_page_paths()`, gases line —
   `get_spare_category("gases")["parts"]` uses `g["slug"]`, while the copper-coil line next to
   it skips parts without a slug (`if c.get("slug")`). Elsewhere a gas without a slug is
   tolerated (`spare_part_url` and `gas_detail` use `.get("slug")`). So if the owner ever adds a gas
   in admin without a slug, the rest of the site keeps working but `/sitemap.xml` would return
   500, and nobody would notice until someone runs `check_site.py --live`. This is the same as
   the old build code and is in line with the design's "fail loudly" choice, so it does not block.
   → Optional: add `if g.get("slug")` to match the copper line. Product, service or category
   slug problems are the existing N2 issue and are out of scope.
2. [nit] `app.py` `render_robots_txt()` — `Allow: /` comes before `Disallow: /admin`. Google and
   Bing (and RFC 9309) use the longest matching rule, so `/admin` is blocked as intended. The
   tester confirmed this with `urllib.robotparser`. A few very old crawlers use the first rule
   that matches and would ignore the Disallow, but that does not matter here because the
   login is the real lock. No action needed. The exact text is fixed by the design and the
   independent check template.
3. [nit] Tester note N1, which is informational only: `Disallow: /admin` is a prefix rule, so it
   would also block a future public page such as `/administration/`. No such page exists. Keep it
   in mind when choosing future URLs.

No must-fix or should-fix findings.

## Requirements check
- R1 (sitemap 200, XML type, valid urlset) → met (AC1 PASS; `application/xml; charset=utf-8`)
- R2 (same page set, from live content, follows admin edits) → met (built on every request from the DB; AC2 and AC6 PASS; same order as the old build)
- R3 (no thank-you, /go/, /admin, 404 or non-200 pages) → met (`NOT_IN_SITEMAP`, `bad_locs`, every loc fetched)
- R4 (full address, trailing /, once, 200) → met (de-duplicated; checked locally, in the build via `check_sitemap()`, and live)
- R5 (lastmod YYYY-MM-DD, today per Q2) → met
- R6 (robots.txt text/plain, same text + `Disallow: /admin` per Q1, configured site URL) → met (AC7 and AC8 PASS)
- R7 (static build keeps both files; cannot drift) → met (one page list in `app.py`; the build fetches from the routes; check_site compares the built files with the app's)
- R8 (`--live` fails on a missing file; local checks cover the routes) → met (NOTE special case removed; AC10 negatives PASS)
- R9 (no new packages, light) → met
- R10 (no URL changes, /go/ works) → met
- R11 (favicon.ico 200, same bytes, icon type, not in sitemap) → met (local part; the live part is checked at deploy)

## Notes for deployment
- **Merge order:** this branch is based on `feature/website-team` (PR #4). Merge PR #4 first, or
  merge this PR knowing that it brings PR #4's commits with it. Merging to `main` puts it live
  within about 5 minutes. No `setup.sh` run, no database step and no new packages are needed.
- **Commit `04-test-report.md`** (and this review) on the branch before the merge. Stage files
  by name: never include the owner's `data/products/05-*.json` or `08-*.json` edits.
- **After going live**, run `.venv/Scripts/python tools/check_site.py --live` to cover AC11 and
  the live part of AC12. It should show all three files returning 200, the exact robots.txt text,
  every sitemap page opening, the favicon bytes matching, and the `www.` redirect working. The
  live sitemap follows the live database, so its page count can differ from the local 152.
  That is expected.
- **Owner action (optional):** resubmit `https://arcooling.in/sitemap.xml` in Google Search
  Console so it stops reporting the error.
- **Watch:** if the owner clears a product's slug (or a gas's slug, see finding 1) in admin,
  `/sitemap.xml` returns 500. This is the existing N2 issue and a good candidate for a later
  admin-validation fix. Also still open, as a separate job: the sample reviews showing on the
  live home page (next candidate 1 in 01).
