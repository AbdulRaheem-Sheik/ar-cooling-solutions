# Test report: Count calls, WhatsApp taps and enquiries, and fix the privacy mismatch (Option A) — PASS

**In short:** the change works. Public pages and the 404 page load the Google tag once. The admin
pages load no Google code and made no Google request in a real browser. A successful send of
either form gives exactly one `enquiry_sent` with the right form and type. Failed sends,
validation errors, and reloading the thank-you page (or going Back and Forward) give none. In
every case the thank-you page opened within about 1 second of FormSubmit's answer: 1–10 ms
normally, and about 1.0 s in the worst case, where Google never answers. No typed value
appeared in any of 86 recorded Google requests. The privacy page is accurate and easy to read
at 320 and 375 px. `check_site.py` passes, and its new checks fail when they should. Nothing
was sent to FormSubmit or to Google Analytics.
AC-A11 can only be checked after release. I found no must-fix or should-fix defects, only
three minor notes.

## Environment
- Branch `fix/analytics-privacy`, HEAD `876447b` (code in `209360f`). I edited no code. The
  working tree was clean at the start. While I was testing, someone else (not me) added an
  "Owner decisions before merge" section to `01-requirements.md`. It is uncommitted.
- `serve.py` (Waitress) on `http://127.0.0.1:8792` with a new throwaway database
  (`AR_DATABASE_PATH` = temp file in the session scratchpad), a 48-character test
  `SECRET_KEY` and throwaway admin credentials (`tadmin` / a test password). Stopped afterwards.
- Headless Edge driven over DevTools, the same harness as the quick-enquiry rounds, extended
  for this task. The scripts `n2setup.py`, `n2tap.py`, `n2forms.py`, `n2admin.py` and
  `n2privacy.py` are in the session scratchpad `tester\` folder. Three network modes:
  - **gtm:** `googletagmanager.com` could serve only `gtm.js?id=GTM-WZFNQQXC` (and
    `gtag/js?id=G-EYB0ZX8K90`, which was never requested). Every other Google tag/analytics
    request (`google-analytics.com/g/collect`, `googletagmanager.com/td` and `/a`,
    `analytics.google.com`, `doubleclick.net`) was intercepted, its URL and body recorded,
    and then **failed**. As a second safety net, the `google-analytics.com`,
    `analytics.google.com` and `doubleclick.net` hosts were also mapped to a dead port.
  - **stall:** like gtm, but the collect requests were left paused for good. They never left
    the browser and never got an answer, which simulates a slow or hanging Google.
  - **block:** `googletagmanager.com` was dead too, so GTM never loaded (an ad blocker, for
    example).
  - In every mode, `formsubmit.co` was mapped to a dead port and failed in DevTools. A
    "successful send" means the page's own `fetch` was stubbed to return
    `{"success":"true"}`. WhatsApp hosts were also dead, so new tabs went nowhere.
- What I saw from Google: with GTM loaded, the container itself sends GA4 hits to
  `www.google-analytics.com/g/collect?v=2&tid=G-EYB0ZX8K90` (POST, with the event details in
  the URL). All of these were recorded and failed.
- **One small Google request did get through** in the first gtm-mode form run. My first
  allow-rule let through any `googletagmanager.com/gtm.js?…` URL, and the tag sent a
  diagnostics ping in that shape (`gtm.js?id=GTM-WZFNQQXC&is_td=1&…&dl=127.0.0.1%2Fenquiry%2F`).
  It carried only the local test page path and the container/measurement IDs, and no
  personal data. It is Tag Manager's own health ping, not a GA4 hit, so it does not appear
  in the owner's reports. After that I narrowed the rule to the exact loader URL. No GA4
  collect request ever went out.

## Regression
`.venv/Scripts/python tools/check_site.py` gave **ALL CHECKS PASSED**, exit code 0 (saved
output: `n2-regress.out`). It covered:
- 153 pages render, and the unknown page gives 404.
- **public pages load the Google tag exactly once**.
- **privacy page explains Google Analytics (no "has no analytics")**.
- 9 share pages, plus the sitemap, robots and favicon checks.
- admin: locked when logged out, the token is needed to log in and save, and **dashboard
  links to an edit page**.
- **admin pages load no Google tag (3 checked)**.
- the static build of 153 pages + 404, with its link and sitemap checks, and the built
  robots/sitemap matching the app.

`check_site.py --skip-build --live --live-url http://127.0.0.1:8792` also gave ALL CHECKS
PASSED, including "live home page loads the Google tag once" and "live /admin/login loads no
Google tag".

## Acceptance criteria

| AC | Result | Evidence |
|---|---|---|
| AC-A1 | **PASS** | `curl` + count of `googletagmanager.com/gtm.js?id=GTM-WZFNQQXC`. Each page had **1** tag, 1 `function gtag()`, 1 `script.js` and 0 `google-analytics.com`: `/` 200, `/services/` 200, `/products/` 200, `/parts/` 200, `/enquiry/` 200, `/enquiry/thank-you/` 200, `/privacy/` 200, `/about/` 200, `/clients/` 200. The 404 pages `/no-such-page/`, `/services/no-such/` and `/go/nope/` also had 1 each. Static build: `_site/index.html`, `404.html`, `privacy/index.html` and `enquiry/thank-you/index.html` had 1 each. The `/go/2026-11-13-1/` share page has 0 tags, as before. |
| AC-A2 | **PASS** | **Source:** `/admin/login`, `/admin` (logged in) and 4 edit pages (`products/split-ac-units`, `spares/copper-coils`, `compressors/copeland`, `services/installation`) had 0 matches for `googletagmanager\|gtag(\|dataLayer\|google-analytics`. None of them has a `<script>` tag at all, and the only external host is `fonts.googleapis.com`. **Browser (`n2admin.py`, gtm mode, so GTM *could* load if asked):** I typed the throwaway login, opened the dashboard and three edit pages, went back to the dashboard each time, and focused fields and clicked `summary`/`button[type=button]` (no saves). Every request went to one of `127.0.0.1:8792`, `fonts.googleapis.com` or `fonts.gstatic.com`. Google tag/analytics requests: **[]**. `typeof gtag / dataLayer / google_tag_manager` was `undefined` for all three. The admin markup uses nothing from `script.js` (checked with grep for `.menu-toggle`, `.reveal`, `#year`, carousels, counters and `data-nav-item`). |
| AC-A3 | **PASS** | 375×800 phone mode, gtm mode, real mouse taps at the element centre, one tap per fresh page load. **Header Call:** at 375 px the header "Call us" (`a.nav-call`) is inside the menu. After opening the menu, a tap gave `en=call_click`, `dl=…/`, `ep.link_text=Call us`. **Bottom bar "Call"** (`a.mobile-cta-call`): `en=call_click`, `dl=…/`, `link_text=Call`. **Body:** home "Call us" button gave `call_click` `dl=…/`. `/services/repair/` "Call us" gave `call_click` `dl=…/services/repair/`. Footer number on `/products/split-ac-units/` gave `call_click` `dl=…/products/split-ac-units/`, `link_text=+91 88013 81405`. At 1280 px, header `a.nav-call` gave `call_click` `dl=…/`, and the body Call on `/services/repair/` gave `call_click` with that page. Each tap gave exactly one `call_click`. `defaultPrevented=false` every time, so the link still works. |
| AC-A4 | **PASS** | Bottom-bar WhatsApp (375) gave `en=whatsapp_click`, `link_text=WhatsApp`, `dl=…/`, and a new tab opened to `wa.me/…`. Contact card on home gave `whatsapp_click` (`WhatsAppMessage us`). The `/services/repair/` body button gave `whatsapp_click` with `dl=…/services/repair/`. The floating button (only visible at desktop width; hidden at 375, where the bottom bar replaces it) gave `whatsapp_click`, `link_text=WhatsApp us` at 1280. GA4's own outbound `click` event also fires (enhanced measurement, as before). **Email** card gave `en=email_click`. |
| AC-A5 | **PASS** | gtm mode, stubbed success, one `enquiry_sent` per send, seen both in the page's `dataLayer` (snapshot taken as the page closed) and in the recorded GA4 hits. Each send then reached `/enquiry/thank-you/`, which showed the right "… enquiry received, Thank you, Zqtest Nameval" text. Each row below is `ep.enquiry_form / ep.enquiry_type`. **Full form:** service via the `/services/repair/` Enquire link gave `full / service`. Product via the `/products/split-ac-units/` link gave `full / product`. Spare via the `/parts/compressors/copeland-zr28k3/` link gave `full / spare`. `/enquiry/` with a category that has no type gave `full / general`. `/enquiry/` with a product category only gave `full / product`. **Quick form:** home with Spare part gave `quick / spare`; Service gave `quick / service`; Product gave `quick / product`; AMC gave `quick / general`; Other gave `quick / general`. `/services/` with Service gave `quick / service`, and `/about/` with Service gave `quick / service`. The hits contain no other `ep.*` details. The gtag call details were exactly `{enquiry_form, enquiry_type, event_timeout:1000}` (plus the callback function). |
| AC-A6 | **PASS** | Both forms in gtm mode and in block mode. **Failure:** FormSubmit blocked showed "Sorry, your enquiry couldn't be sent (Failed to fetch). Please try again, or call us on +91 88013 81405." A stubbed 500 answer showed "…couldn't be sent (fake error)…". The page stayed put, with 0 `enquiry_sent` in `dataLayer` and 0 in the GA hits. **Validation:** full form with an empty name moved focus to `name` ("Please fill out this field."). Quick form with an empty mobile moved focus to `phone`; with no topic, focus went to `topic` ("Please select an item in the list."). In all three, the `fetch` was not called and there was no `enquiry_sent`. **Thank-you page:** after a counted success, I ran Reload, Back (to `/enquiry/`), Forward, then Reload again. The GA hits during these steps were only `page_view`/`scroll` for `/enquiry/thank-you/`, with **no `enquiry_sent`**, and the thank-you page's `dataLayer` had none. |
| AC-A7 | **PASS** | Time from the stubbed success answer to the start of the thank-you navigation, measured as `(Date.now() − performance.now())` on the thank-you page minus the timestamp written by the stub. **Block mode** (GTM never loads): 13 successes on both forms took **2–10 ms**, with no `enquiry_sent` pushed (`google_tag_manager` absent, so it leaves at once). **gtm mode, collect failed:** 2–10 ms. **stall mode** (collect hangs forever): **1–3 ms** (GA4 calls back once the hit is queued). **The "callback never comes" case** (GTM's `dataLayer.push` replaced by a no-op): full form **1004 ms**, quick form **1015 ms**. The `setTimeout` fallback works. **"gtag missing"** (`window.gtag = 1`): went at once with no event, in both modes. Every case reached the thank-you page exactly once. Call and WhatsApp links with Google blocked: all 6 taps (bottom-bar Call/WhatsApp, menu header Call, body Call ×2, body WhatsApp) had `defaultPrevented=false`, and the WhatsApp taps opened the `wa.me` tab. |
| AC-A8 | **PASS** | Test values: name "Zqtest Nameval", mobile 9000000001, email zq.test@example.invalid, area "Zqarea Locality", company "Zqcompany Pvt", details/comments/message "Zq… textval", plus the generated `AR-…` reference. In the main gtm run I searched all **86** recorded Google requests (URL and body, raw and URL-decoded) for `Zq`, `zq`, `Nameval`, `9000000001`, `900000`, `example.invalid`, `Locality`, `textval`, `Zqcompany` and `AR-2`: **0 matches**. The tap events carried only our own link text. On the email link, GA4's automatic redaction showed `link_text=(redacted)` (see note 2). |
| AC-A9 | **PASS** | The `/privacy/` text has no "has no analytics". "Last updated 17 November 2026" is shown. There is a new section "Visitor statistics (Google Analytics)". It names Google Analytics, the `_ga` and `_ga_EYB0ZX8K90` cookies, "last up to 2 years", and says "**What you type into the enquiry form is not sent to Google Analytics.**" It also says Signals and ad personalisation are off, that data may be processed outside India, and that detailed statistics are kept for 14 months. Opt-out: the add-on link, block/clear cookies, private window. "Cookies and other services" now says "The only cookies are the Google Analytics ones described above. We don't use advertising cookies." The session-storage and Google Fonts items are unchanged. All external links have `target="_blank" rel="noopener noreferrer"`. `tools.google.com/dlpage/gaoptout`, `policies.google.com/privacy` and `policies.google.com/technologies/partner-sites` all return 200. **Readability:** at 375 px the page width is 375 (no sideways scroll, no element past the edge); list text is 15 px with 26 px line height; `_ga_EYB0ZX8K90` fits. At 320 px it is the same, with page width 320. At 1280 px the text column is 738 px. Screenshot: `n2-privacy-375.png` in the scratchpad `tester\` folder (see note 1). |
| AC-A10 | **PASS** | `check_site.py` passes (see Regression). Negative tests on a scratch copy (`git archive HEAD` into the scratchpad, `--skip-build`), each restored afterwards: snippet put back in `admin_login.html` gave **FAIL** "admin pages load no Google tag (/admin/login: googletagmanager.com, gtag(, dataLayer)", exit 1. In `admin_edit.html`: FAIL on `/admin/products/split-ac-units/edit`. A `google-analytics.com` script in `admin_dashboard.html`: FAIL on `/admin: google-analytics.com`. The snippet twice in `base.html`: FAIL "public pages load the Google tag exactly once (/: 2; …)". "has no analytics" back in `privacy.html`: FAIL on the privacy check. The clean copy gave exit 0 before and after. `build_static.py` passes as part of `check_site.py`. |
| AC-A11 | **NOT TESTED (after release)** | This can only be checked after merging. Pre-merge baseline: the live `https://arcooling.in/admin/login` still has the old snippet (4 matching lines, read-only `curl`). After merge, the new `--live` check must turn from FAIL to PASS. The new `--live` checks already pass against the local server. Seeing the events in GA4 Realtime is for the owner or deployer. |

Shared requirements:
- **S1 / S2:** The only server-side change is `PRIVACY_UPDATED` in `app.py`.
  `requirements.txt`, `store.py`, `serve.py` and `deploy/` are unchanged.
- **S3:** No route changes. The sitemap checks pass. `/privacy` redirects 308 to `/privacy/`,
  and `/go/<id>` redirects 308 to `/go/<id>/`, as before.
- **S4:** See AC-A2.
- **S5:** See AC-A9.
- **S6:** See Regression and AC-A10.
- **S7:** Forms and links work with Google blocked (AC-A7). I did not run the no-JS path in a
  browser this round. Its markup is unchanged (`method="post"`,
  `action="https://formsubmit.co/enquiry@arcooling.in"` on both forms), and
  `_contact.html` / `product_enquiry.html` are not in the diff.
- **Footer link:** "Privacy & cookies" (`Privacy &amp; cookies` in the source) appears once
  on every public page and the 404 page, and is visible at 375, 320 and 1280 px.

## Edge cases
- **Tampered quick-form topic** (option value changed to `toString`): `enquiry_type=general`.
  No function and no free text was sent.
- **The enquiry page address** sent with `enquiry_sent` includes the Enquire-link query
  string (e.g. `?service=repair&category=Repair&product_description=Repair+service…&comments=Please+contact+me…`).
  This is our own prefilled text, not typed text; typed values never reach the URL.
- **Unknown URLs give 404**, with the tag once. **Admin without login:** `/admin` and the
  edit page redirect 302 to `/admin/login`. **Login without CSRF token:** 400.
  **Trailing slash:** `/privacy` redirects 308.
- **No double count:** each success pushed exactly one `enquiry_sent` and produced exactly
  one GA hit. The `gone` guard held: one navigation per send in all modes, including the
  1-second fallback.
- **GA4's automatic `form_start` / `form_submit`** did not appear in any hit during these
  sends.

## Defects
None must-fix or should-fix.

1. **Minor (existing before this change, not introduced by it):** at 375 px, the fixed
   social "follow" buttons on the right edge (in, X, f, Instagram) cover the end of a few
   lines on the privacy page. For example, "on yo[ur]", "They hol[d]" and "name" in the
   `_ga` bullet are hidden (see `n2-privacy-375.png`). The text can still be read by
   scrolling, and the same overlay is on every page. This is a follow-up for the backlog,
   not part of this task.
2. **Minor (information for the owner notes):** GA4 automatically redacts email addresses,
   so `email_click` from the email links arrives with `link_text=(redacted)`. The count still
   works, but the owner's report will not show which email link was tapped.
3. **Minor (information):** when Tag Manager loads, it also sends its own diagnostics pings
   (`googletagmanager.com/td`, `/a`, and `gtm.js?…&is_td=1`). These contain the page address
   and container ID. The privacy page already says Google receives the page address, so
   this is covered. I mention it only so nobody is surprised to see these requests in dev
   tools.
