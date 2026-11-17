# Deployment: Count calls, WhatsApp taps and enquiries, and fix the privacy mismatch (backlog N2)

## Prepare (2026-11-17)

- **Branch:** `fix/analytics-privacy` (code at a8ecbbc; docs commits after it).
- **Verdicts:** 04-test-report.md = PASS (retest round 1 at a8ecbbc; AC-A11 is post-merge by
  design). 05-review.md = APPROVE (re-review round 1).
- **PR link:** see `pr8url.txt` in the deployer's scratchpad and the deployer's reply (compare
  `main...fix/analytics-privacy`, quick_pull).
- **Server steps:** none beyond the usual auto-pull. No routes, packages, database, `data/` or
  `setup.sh` changes.
- **Rides along:** b18faa8 (docs only: `docs/work/2026-11-16-quick-enquiry-form/06-deployment.md`,
  the N1 verify record) was committed after PR #7 merged, so it reaches `main` with this PR.

### Tag Manager container re-checked (deployer, 2026-11-17)
Fetched `https://www.googletagmanager.com/gtm.js?id=GTM-WZFNQQXC&cb=<timestamp>` (546,893 bytes,
`"version":"2"`):
- `__ogt_1p_data_v2` (user-provided data) has `"vtp_isEnabled":false`: **off**.
- `__ccd_ga_regscope` has `GOOGLE_SIGNALS` with `"disallowAllRegions":true`: **Signals off**.
- Only measurement ID is `G-EYB0ZX8K90`; **no `AW-` or `DC-` IDs** (no Ads / Floodlight).

### Before merging
- Owner's Google settings are done (see "Owner's Google settings done" in 01-requirements.md):
  retention 14 months, Signals off, GA4 user-provided data off, no Google Ads link, Tag Manager
  "Allow user-provided data capabilities" off and published as container Version 2.
- `PRIVACY_UPDATED = "17 November 2026"` (`app.py:879`). If the merge happens on a later day,
  update it on this branch first so the privacy page date matches the merge date.

### After merging
- **Deployer (verify):** confirm the server runs the merge commit; `check_site.py --live` must
  pass, including "live /admin/login loads no Google tag" (FAIL today, before the merge);
  `/privacy/` shows the new section and footer link "Privacy & cookies"; check the
  `ar-cooling` journal for errors.
- **Owner, in GA4, after the first real enquiry** (from 02-design.md "Deployment notes"):
  1. Admin → Events / Key events: mark `enquiry_sent`, `call_click` and `whatsapp_click` as key
     events (`enquiry_sent` can also be created as a key event by name before it appears).
  2. Admin → Custom definitions: add event-scoped custom dimensions `enquiry_form` and
     `enquiry_type` (optional: `link_text`). They count only from the day they are created.
  3. Optional: a saved Exploration / Library report, "month, page path × event count" for the
     three key events plus Users, with an optional monthly email.
  4. Optional: define internal traffic to exclude the owner's own visits; add a second trusted
     Google account as Administrator.
- **One real test enquiry** (marked "TEST – please ignore") after `enquiry_sent` is a key event:
  its `collect` hit should contain only `ep.enquiry_form` / `ep.enquiry_type`, with no `em`,
  `ec_*` or `upd*`. Only with the owner's go-ahead.
- **Owner notes:** counts are a minimum (ad blockers, opt-outs, JavaScript off). Use
  `enquiry_sent`, not GA4's `form_submit` (which also counts failed sends). `email_click` arrives
  with `link_text=(redacted)`. Tell the team before changing any Google setting, because the
  privacy page depends on them.

### Follow-ups (non-blocking)
1. Social share buttons overlap text at 375 px width.
2. Privacy page: add a note that embedded Google Maps also sends the visitor's IP address to Google.
