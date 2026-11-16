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
