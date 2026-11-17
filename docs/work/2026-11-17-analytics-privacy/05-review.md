# Review: Count calls, WhatsApp taps and enquiries, and fix the privacy mismatch (Option A) — APPROVE (re-review round 1; owner steps before merge)

## Summary
The code is good. It is small and follows the existing patterns:
- The three admin templates no longer load the Google tag or `script.js`. I confirmed this in
  the source, in `check_site.py`, and in the tester's browser run (no Google requests at all
  from admin pages).
- `enquiry_sent` only sends two fixed words. In the quick form, `typeKeys` is checked with an
  own-key test. In the full form, `COUNTED_TYPES.includes` is used. So nothing the visitor
  typed can get into the event. The event fires only on the success path, after the
  `try/catch` that `return`s on failure. The `gone` flag makes sure the redirect happens
  only once.
- The new `check_site.py` checks are sound. They fail when they should: a missing page
  counts as 0 tags and fails, a missing live `/admin/login` fails as "page missing", and the
  new "dashboard links to an edit page" check stops the edit-page check from being quietly
  skipped.
- `check_site.py` passes on the branch (I re-ran it: ALL CHECKS PASSED, static build of 153
  pages + 404).
- No secrets or visitor data are in the diff. The only phone and email in the docs are the
  business's own public ones.

I compared the privacy page with what the GTM container and the browser actually do. I
fetched the public `gtm.js?id=GTM-WZFNQQXC` and ran a local check through the tester's
harness, in which every Google collect request was recorded and then blocked. Most of the
page is accurate:
- The only cookies set are `_ga` and `_ga_EYB0ZX8K90`, both about 2 years. There is no
  `_gcl_au`, and our own code sets no cookie on public pages.
- Signals is off in the container (`GOOGLE_SIGNALS disallowAllRegions: true`).
- `enquiry_sent` hits carry only `ep.enquiry_form` / `ep.enquiry_type`.
- Page titles never contain the visitor's name.

Two sentences, however, promise more than the site or its Google settings deliver. The
whole point of this task is that every sentence on the privacy page is true (S5), so both
must be fixed before merge. Both are small text changes, or one Google setting plus a check.

## Findings

1. **[must-fix] templates/privacy.html:54 — two of the three "opt out" methods don't opt you
   out.**
   - A private / incognito window still loads Google Analytics and sends every page view.
     The `_ga` cookie only disappears when the window is closed.
   - Clearing cookies does the same thing: the next visit is counted as a new visitor.
   - Blocking cookies stops the cookies, but the Google script still loads and still sends
     page views.

   Only the opt-out add-on (or a tracker/ad blocker) stops the counting.
   → Reword the bullet, for example:
   "**To stop being counted:** install the [Google Analytics opt-out browser add-on](…), or
   use a browser or add-on that blocks trackers. Clearing or blocking cookies, or using a
   private / incognito window, stops your visits being linked together, but each visit is
   still counted. The website works the same either way."
   The owner approved the current wording, so they need to approve this one changed bullet
   again.

2. **[must-fix] templates/privacy.html:52 — "ad personalisation [is] turned off" has not
   been checked, and the evidence points the other way.**
   - Every GA4 hit I recorded carries `npa=0`, which means the hit is *not* marked as
     non-personalised.
   - The container's regional settings cover only `DEVICE_AND_GEO` and `GOOGLE_SIGNALS`.
     There is nothing about ads personalisation.
   - The owner's agreed pre-merge step (01, "Owner decisions before merge") confirms only
     that Signals is off.

   → Either:
   (a) before merge, the owner opens GA4 → Admin → Data collection and modification → Data
   collection → "Advanced settings to allow for ads personalization", turns it off for all
   regions, and confirms GA4 → Admin → Product links shows no Google Ads link. Or:
   (b) change the sentence to what is already true, e.g. "We do not use Google Analytics
   for advertising: it is not linked to Google Ads, and Google Signals is turned off."
   (b) is the safer text whatever the owner does, because it states only things we have
   checked.

3. **[should-fix, do before merge] GTM container — automatic "user-provided data"
   detection is switched on.** In `gtm.js`, the `__ogt_1p_data_v2` tag has
   `isEnabled: true`, `isAutoEnabled: true`, `autoEmailEnabled`, `autoPhoneEnabled` and
   `autoAddressEnabled`, and calls `internal.detectUserProvidedData`. This Google feature
   scans the page for email addresses and phone numbers (for example in our form fields)
   and can send them to Google in hashed form.
   - In my local check, nothing was attached. That covered `enquiry_sent`, and also
     `qualify_lead`, which the container already treats as a key event (`_c=1`). No
     `em` / `ec_*` / `upd` parameters were sent and nothing went to `google.com/ccm`.
   - So the line 51 promise ("What you type into the enquiry form is not sent to Google
     Analytics") holds today. But it rests on Google's current behaviour, not on a setting
     we control, and the owner is about to mark `enquiry_sent` as a key event.
   - The tester's AC-A8 search looked for the raw typed values, so it could not have found
     hashed ones.

   → The owner turns off GA4 → Admin → Data collection → "User-provided data collection"
   (and, if shown, the Google tag's "automatic detection of user-provided data"). The
   deployer then re-fetches `gtm.js?id=GTM-WZFNQQXC` and confirms that `__ogt_1p_data_v2`
   is gone or has `"vtp_isEnabled":false`.

4. **[should-fix] static/js/contact.js:37-38 and static/js/enquiry.js:161-162 — start the
   1-second safety timer before calling `gtag`.** The timer is "the real guarantee", but it
   is only set *after* `gtag(...)` returns. Once GTM has loaded, `gtag` pushes into GTM's own
   `dataLayer.push`. If that ever throws, the redirect never happens. The visitor's enquiry
   has already been sent, but they are left on a disabled "Sending…" button and may send it
   again.
   → Swap the two lines in both files (`setTimeout(go, 1000);` first, then `gtag(...)`).
   There is no other change in behaviour.

5. **[nit] templates/privacy.html:50 — the list of what Google receives is shorter than what
   the hits carry.** The hits also include the page title, the page the visitor came from,
   screen size and browser language. When Tag Manager loads, it also sends its own small
   diagnostics requests with the page address. → If the bullet is reopened for finding 1/2
   anyway, consider "the page address and title, the page you came from, your type of
   device, browser and screen…". Line 62 could say "fonts and the Google Analytics script"
   so that the IP-address sentence covers `googletagmanager.com` too.

6. **[nit] 04-test-report.md, AC-A8 — method note.** A search for raw typed values cannot
   find hashed data. For future rounds, also check that the hits have no `em`, `ec_*` or
   `upd*` parameters and that nothing is sent to `google.com/ccm`.

## Requirements check
| Req | Result |
|---|---|
| S1 no server-side storage/cookies | met (only `PRIVACY_UPDATED` changed; no session cookie on public pages) |
| S2 no new packages/paid services | met |
| S3 URLs, `/go/<id>/`, sitemap, robots unchanged | met (sitemap/robots checks pass; footer link keeps `/privacy/`) |
| S4 admin pages load no Google tag | met (source, check_site, tester's browser run) |
| S5 privacy text matches reality, new date | **not met**: findings 1 and 2 (date is correct) |
| S6 check_site / build pass, new checks | met (re-run: ALL CHECKS PASSED; negative tests in 03/04) |
| S7 forms/links work with Google blocked, no-JS unchanged | met (finding 4 is about making this more robust) |
| A1 tag once on public pages, none on admin | met |
| A2 / A3 `call_click`, `whatsapp_click` (`email_click` kept) | met (unchanged code, verified by tester) |
| A4 `enquiry_sent` only on success, at most 1 s, works when blocked | met |
| A5 no personal data in events | met in code; see finding 3 for the container setting |
| A6 privacy page tells the truth | **not met**: findings 1 and 2 |
| A7 no banner, "Privacy & cookies" footer link | met |
| A8 owner's monthly view | owner steps in 02 (not code); deployer writes owner notes |
| A9 snippet unchanged | met (byte-for-byte; owner step 0 confirmed events arrive) |

## Notes for deployment
- **Before merge (owner, in Google's screens):**
  - set GA4 data retention to 14 months (the privacy page says so);
  - confirm Signals is off;
  - for finding 2 (a): turn ads personalisation off for all regions, and confirm there is no
    Google Ads link;
  - for finding 3: turn user-provided data collection off.
- **Before merge (developer):** fix findings 1 and 2 (text) and 4 (swap two lines). The owner
  re-approves the changed privacy bullets. If the merge slips past 17 November, update
  `PRIVACY_UPDATED`.
- **Deployer:** after the owner's changes, re-fetch the public `gtm.js?id=GTM-WZFNQQXC` and
  confirm that Signals is still disallowed and that `__ogt_1p_data_v2` is off or gone. After
  release, run `check_site.py --live`. Today the live `/admin/login` still has the tag, so
  that check must turn from FAIL to PASS.
- **After the owner marks `enquiry_sent` as a key event:** send one real test enquiry,
  marked "TEST – please ignore", and check its `collect` hit in dev tools. It should contain
  only `ep.enquiry_form` / `ep.enquiry_type`, with no `em`, `ec_*` or `upd*`.
- **Commit:** `04-test-report.md` and this file are uncommitted, as expected. The
  `01-requirements.md` "Owner decisions before merge" edit is uncommitted too. Commit all
  three by name.
- **Owner notes:** counts are a minimum (ad blockers and opt-outs are not counted).
  `email_click` arrives with `link_text=(redacted)`. Use `enquiry_sent`, not `form_submit`.
  Tell the team before changing any Google setting, because the privacy page depends on
  those settings.

---

# Re-review (round 1) — APPROVE

Reviewed `git diff 1cb1591..a8ecbbc` (branch `fix/analytics-privacy` at `a8ecbbc`), the owner
decisions at the end of 01 and the Rework log in 03. The commit contains only
`03-implementation.md`, `contact.js`, `enquiry.js` and `privacy.html` (no `data/` edits).
`node --check` passes on both JS files. Tester re-run is in progress separately (04).

## Earlier findings
| # | Result |
|---|---|
| 1 must-fix, opt-out bullet | **Resolved.** `templates/privacy.html:54` matches the owner-approved wording in 01 word for word; the add-on link is unchanged. |
| 2 must-fix, ads sentence | **Resolved.** Line 52 now says only "not linked to Google Ads, and Google Signals is turned off". Re-fetched `gtm.js?id=GTM-WZFNQQXC` today: `GOOGLE_SIGNALS disallowAllRegions: true` and `allow_google_signals: false`; no `AW-` or `DC-` (Google Ads / Floodlight) IDs in the container. A GA4 → Google Ads product link cannot be seen from `gtm.js`, so the owner confirms it (step 3 below). |
| 3 should-fix, user-provided data | **Owner step, still open.** Today's `gtm.js` still has `__ogt_1p_data_v2` with `vtp_isEnabled: true`, `vtp_isAutoEnabled: true`, `vtp_autoPhoneEnabled: true`. Must be switched off before merge (step 1) and re-checked by the deployer. |
| 4 should-fix, timer order | **Resolved.** `static/js/contact.js:39-44` and `static/js/enquiry.js:163-168`: `setTimeout(go, 1000)` now runs first, and `gtag` is wrapped in `try/catch` that calls `go()`. With the `gone` guard the page still navigates exactly once (callback, timer or catch). The early `return go()` when Google is blocked is unchanged. The two copies are identical. |
| 5 nit, "Google receives" list | **Resolved.** Line 50 now lists page address and title, referring page, device type, browser, screen size and rough location. |
| 6 nit, tester method | Left to the tester (not code). |

## Whole privacy page re-checked
Every sentence was compared with the code and Google's behaviour:
- Lines 23-44 (what we collect, FormSubmit, WhatsApp, use, retention, rights): unchanged from
  `main` and still match the forms and `contact.js`/`enquiry.js` (FormSubmit only; nothing
  stored on our server).
- Line 49 (two cookies, random ID, up to 2 years) and line 60 ("The only cookies are the
  Google Analytics ones"): true for our pages. I also checked the Google Maps embed in
  `_contact.html` (on home, about, clients and services): loading it in a fresh headless Edge
  profile set **no** Google cookies, and the embed response has no `Set-Cookie`.
- Line 51 (form contents not sent): true in code and in the round-0 hit capture; it depends on
  Google's own detection being off, so owner step 1 is what makes it safe for the future.
- Line 52: see finding 2 above.
- Line 55 (14 months): true only once the owner sets GA4 retention (step 2).
- Line 61 (session storage, cleared when the tab closes): matches `sessionStorage` use in
  `contact.js:96`, `enquiry.js:268`, `enquiry_thanks.html:34`; no `localStorage` or
  `document.cookie` anywhere in our JS.
- "Last updated 17 November 2026" (`app.py:879`) is correct for a merge today.

## New finding
7. **[nit] templates/privacy.html:62 — Google Maps is not mentioned.** The map on the home,
   about, clients and services pages is loaded from Google, so Google gets the visitor's IP
   address from it too, just like Google Fonts (and Tag Manager). Nothing on the page is
   false; it is just incomplete, and this was already so on `main`. → In a later change, e.g.
   "The site loads its fonts from Google Fonts, and the map from Google Maps, so Google
   receives your device's IP address when a page loads…". Does not block.

## Requirements check (changes since round 0)
- S5 privacy text matches reality → **met in code**; lines 51, 52 and 55 rely on the owner
  steps below being done before merge.
- A6 privacy page tells the truth → **met** (same condition).
- S7 forms work with Google blocked → met, now more robust (finding 4).
- All other rows unchanged from round 0: met.

## Owner's steps before merge (all in Google's screens; nothing on the server)
1. **GA4 → Admin → Data collection and modification → Data collection → turn OFF
   "User-provided data collection"** (and, if the Google tag settings show it, "automatic
   detection of user-provided data"). Needed for line 51 to stay true.
2. **GA4 → Admin → Data retention → set event data retention to 14 months** and save.
   Needed for line 55.
3. **Confirm Google Signals is OFF** (GA4 → Admin → Data collection) and **GA4 → Admin →
   Product links → Google Ads links shows no link.** Needed for line 52.
4. Tell the team before changing any of these settings later: the privacy page depends on them.

## Notes for deployment
- **Deployer, after the owner's steps and before merge:** re-fetch the public
  `https://www.googletagmanager.com/gtm.js?id=GTM-WZFNQQXC` and confirm (a)
  `__ogt_1p_data_v2` is gone or has `"vtp_isEnabled":false`, (b) Signals is still
  `disallowAllRegions: true`, (c) still no `AW-`/`DC-` IDs. Note that Google may take a few
  minutes to publish the setting change into `gtm.js`. Do not merge while (a) fails.
- Wait for the tester's round-1 result in 04 before merging.
- If the merge slips past 17 November, update `PRIVACY_UPDATED` in `app.py`.
- After release: `check_site.py --live` (live `/admin/login` must turn from FAIL to PASS),
  and one real test enquiry marked "TEST – please ignore", checking its `collect` hit has only
  `ep.enquiry_form` / `ep.enquiry_type` and no `em`, `ec_*` or `upd*`.
- Commit `04-test-report.md` and this file by name.
