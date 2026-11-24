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

## Verify (2026-11-17)

**Result: LIVE and working.** Nothing to revert.

- **Merge:** PR #8 merged to `main` as **3f009e0** (17 Nov 2026, 12:49 IST);
  `git merge-base --is-ancestor fix/analytics-privacy origin/main` is true.
- **Server:** `ar-cooling-update` log: "Updated main de55f55 -> 3f009e0" at 07:19:32 UTC
  (12:49 IST). `/opt/ar-cooling` is on **3f009e0**; `ar-cooling` restarted at 07:19:32 UTC and
  is active ("running at http://127.0.0.1:8080"). No errors in the journal after the restart.
  - Seen in the journal before the restart (00:45 UTC, not caused by this change): a short burst
    of `waitress.queue: Task queue depth is 3–8` warnings, a brief traffic spike that the
    site handled. Worth watching; nothing to do now.
- **Extra deployment steps:** none (no `setup.sh`, packages, database or `data/` changes).

### Live checks
Only plain page fetches were used (no browser, no JavaScript), so **no Google Analytics hits
were made and no enquiries were sent.**

| Check | Result |
|---|---|
| `tools/check_site.py --live` | **ALL CHECKS PASSED**: 152 live sitemap pages open, robots/sitemap/favicon OK, "live home page loads the Google tag once" PASS, "live /admin/login loads no Google tag" PASS (failed before the merge), www redirect OK |
| `/privacy/` section "Visitor statistics (Google Analytics)" | Present (cookies `_ga` / `_ga_EYB0ZX8K90`, 2 years, form contents not sent, 14 months) |
| Opt-out bullet | Matches the owner-approved wording in 01-requirements.md word for word; add-on link (tools.google.com/dlpage/gaoptout) opens (200) |
| "not linked to Google Ads, and Google Signals is turned off" | Present |
| "Last updated 17 November 2026" | Present (matches the merge date) |
| Footer link | Reads "Privacy & cookies" (`/privacy/`) |
| `/admin/login` | 0 matches for googletagmanager / gtag / dataLayer / script.js |
| Live `static/js/enquiry.js`, `static/js/contact.js` | Byte-for-byte the same as `origin/main`; `/enquiry/` loads enquiry.js, the home page loads contact.js |

### Owner: GA4 steps once the first real `enquiry_sent` appears
Check under GA4 → Reports → Realtime or Engagement → Events. Then:
1. **Key events.** Admin → Data display → Events (or Key events): turn on "Mark as key
   event" for `enquiry_sent`, `call_click` and `whatsapp_click`. (`enquiry_sent` can also be
   added as a new key event by typing the name before it first appears.)
2. **Custom dimensions.** Admin → Data display → Custom definitions → Create custom
   dimension, scope **Event**:
   - Name "Enquiry form", event parameter `enquiry_form`
   - Name "Enquiry type", event parameter `enquiry_type`
   - Optional: "Link text", parameter `link_text`

   These only count from the day you create them, so create them soon.
3. **Optional monthly report.** Explore → Free form: rows "Month" and "Page path", values
   "Event count" filtered to the three key events, plus "Users". Save it, and if you want,
   use Share / Schedule email for a monthly copy.
4. Optional: set up internal traffic so your own visits are left out, and add a second
   trusted Google account as Administrator.

Reminders: the counts are a minimum (ad blockers, opt-outs, JavaScript off). Use
`enquiry_sent`, not GA4's own `form_submit`, which also counts failed sends. Tell the team
before changing any Google setting, because the privacy page depends on them.

### Follow-ups
- One labelled test enquiry ("TEST – please ignore") to confirm the hit carries only
  `enquiry_form` / `enquiry_type`: **only with the owner's go-ahead**, after `enquiry_sent` is
  a key event. Not done.
- Carried over: share buttons overlap text at 375 px; privacy note that embedded Google Maps
  also sends the visitor's IP address to Google.
- Keep an eye on the waitress queue-depth warnings if they come back often.
