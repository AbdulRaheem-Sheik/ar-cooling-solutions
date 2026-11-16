# Deployment: Serve sitemap.xml, robots.txt and favicon.ico on the live site

## Prepare (2026-11-16)
- Branch: `fix/live-sitemap-robots`, pushed to `origin`. Base for the PR is `main`.
- Verdicts: `04-test-report.md` says **PASS** and `05-review.md` says **APPROVE**, with no must-fix
  or should-fix findings. Both were committed on the branch together with this file. The owner's
  uncommitted `data/products/05-*.json` and `08-*.json` edits were not staged.
- Merge order: this branch is based on `feature/website-team` (PR #4, `325b38c`). Merge PR #4
  first. Otherwise this PR also brings in PR #4's commit.
- PR link: opened by the owner from the compare link in the deployer's report. The link has the
  title and body filled in already.
- Extra deployment steps: **none**. This was confirmed from `02-design.md` ("No setup.sh run, no
  live DB step, no new packages"): no Caddy or `deploy/` change, no data or schema change.
  Merging to `main` puts it live within about 5 minutes through `ar-cooling-update`.
- After the merge (verify phase): confirm the server is on the merge commit, run
  `.venv/Scripts/python tools/check_site.py --live` (AC10-AC12 live part, every sitemap loc 200,
  exact robots.txt text, favicon bytes, `www.` redirect), and check `journalctl -u ar-cooling`.
- Follow-ups (non-blocking review nits): (1) add `if g.get("slug")` to the gases line in
  `public_page_paths()`; (2) the order of `Allow: /` and `Disallow: /admin` needs no action;
  (3) `Disallow: /admin` is a prefix rule, so keep it in mind for future URLs; (4) existing issue N2:
  clearing a slug in admin makes `/sitemap.xml` return 500. Optional owner action: resubmit
  the sitemap in Google Search Console.

## Verify (2026-11-16)
- Merge: `fix/live-sitemap-robots` is an ancestor of `origin/main` (`git merge-base --is-ancestor`
  OK). The owner merged PR #4 (`3ed2fe6`) first, then PR #5. Merge commit: `58cba28` ("Merge pull
  request #5 from AbdulRaheem-Sheik/fix/live-sitemap-robots").
- Server: `sudo systemctl start ar-cooling-update` was run. `/opt/ar-cooling` is on `58cba28`.
  `ar-cooling` is `active`. It restarted at 04:13:29 and logged "running at http://127.0.0.1:8080"
  at 04:13:31.
- Extra deployment steps: none (as in `02-design.md`). None were run.
- `tools/check_site.py --live` (run from local `main` at `58cba28`): **ALL CHECKS PASSED**, exit 0.
  This covers the local app (153 pages, sitemap of 152 pages, robots.txt, favicon, admin, static
  build) and the live site (17 live pages and files, exact robots.txt text, a valid sitemap of 152
  pages with all 152 loc URLs returning 200, favicon, and the www redirect).
- AC11 live, checked by hand:
  - `https://arcooling.in/robots.txt`: 200, `text/plain; charset=utf-8`. The body is exactly
    `User-agent: *` / `Allow: /` / `Disallow: /admin` / blank line /
    `Sitemap: https://arcooling.in/sitemap.xml`.
  - `https://arcooling.in/sitemap.xml`: 200, `application/xml; charset=utf-8`. It is a `urlset`
    with 152 `<loc>` entries, full `https://arcooling.in/...` addresses, and lastmod `2026-11-16`.
  - `https://www.arcooling.in/sitemap.xml` and `/robots.txt`: 301 to the same path on
    `https://arcooling.in/`.
- AC12 live: `https://arcooling.in/favicon.ico` returns 200, `image/vnd.microsoft.icon`, 7077 bytes.
  The SHA-256 `0bdab012...d83362` is identical to `static/favicon.ico` (`cmp` equal).
- Logs: `journalctl -u ar-cooling` shows no errors, tracebacks or exceptions since the restart.
  The earlier entries are only the usual `waitress.queue` depth warnings from Nov 15.
- Live status: **LIVE and OK**. No revert needed.
- Follow-ups: the non-blocking review nits listed under Prepare. The owner can optionally
  resubmit `https://arcooling.in/sitemap.xml` in Google Search Console.
