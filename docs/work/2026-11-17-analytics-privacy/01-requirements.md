# Count calls, WhatsApp taps and enquiries, and fix the privacy mismatch (backlog N2)

## Goal
"I want to know how many people call, WhatsApp or send an enquiry from the website, and from
which page, and I want the privacy page to tell visitors the truth about it." If the owner
would rather not measure at all, the site should have no tracking and say so (Option B).

## Users & context
- **Visitors:** people in Hyderabad looking for AC installation, repair, gas refilling, AMC
  and spare parts, mostly on phones. They tap Call, WhatsApp or send the enquiry form. They
  read the privacy page rarely, but what it says must be true.
- **Owner:** not a developer. Wants a simple monthly answer to "how many calls, WhatsApp
  chats and enquiries did the website bring, and from which pages?" on a phone or laptop.
- **Admin user:** uses `/admin` to edit content. These visits are not customers and should
  not be sent to Google.

## Current behaviour

### Where the Google tag loads
The same snippet sits at the very top of `<head>` in four templates:

| Template | Pages | Also loads `static/js/script.js` |
|---|---|---|
| `templates/base.html` (lines 5-11) | every public page (all templates `{% extends "base.html" %}`: home, products, services, parts, compressors, copper, gas, clients, about, enquiry, thank-you, privacy, 404) | yes |
| `templates/admin_login.html` (lines 4-10) | `/admin/login` | yes (line 11) |
| `templates/admin_dashboard.html` (lines 4-10) | `/admin` | yes (line 11) |
| `templates/admin_edit.html` (lines 4-10) | `/admin/<collection>/.../edit` | yes (line 11) |

The `/go/<id>/` share pages (`render_share_page` in `app.py`) have **no** tag. They redirect
straight to the target page, which then counts the visit.

The snippet:
```html
<script async src="https://www.googletagmanager.com/gtm.js?id=GTM-WZFNQQXC"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
</script>
```
In plain words, this loads Google's tag container GTM-WZFNQQXC and creates the `gtag()`
helper. There is no `gtag('config', …)` and no `gtag('consent', …)` line in our code. The
measurement settings come from the container, which is configured in Google's own website.
The snippet is a mix of the "Google Tag Manager" and "gtag.js" styles, and there is no
`<noscript>` part.

### What the container does (public file fetched 2026-11-17)
`https://www.googletagmanager.com/gtm.js?id=GTM-WZFNQQXC`:
- **One destination: Google Analytics 4, measurement ID `G-EYB0ZX8K90`.** No Google Ads
  (`AW-`) or Floodlight (`DC-`) IDs, no old Universal Analytics (`UA-`), and no other
  vendors (Facebook, Clarity, Hotjar: none found).
- Tags fire on page load (`gtm.init` / `gtm.js`). Tag types found: GA4 destination, Google
  tag, page view, and GA4 **"enhanced measurement"**: scroll, outbound clicks, form start /
  form submit, file downloads, site search and video. It also includes conversion marking,
  automatic redaction (removes things like email addresses from page addresses), and
  user-provided-data / auto-events settings.
- **Google Signals is turned off for all regions** (`disallowAllRegions: true`), so no
  cross-device ad tracking or ad personalisation.
- **No consent mode default is set** in the container or our code. GA4 therefore sets its
  normal first-party cookies (`_ga` and `_ga_EYB0ZX8K90`, which last up to about 2 years) on
  every visitor's first page view, with no banner.
- The fetch only read the first part of a 547 KB file. The architect should check the rest,
  or check the GTM / GA4 admin screens if the owner can give access.

### What the site sends to Google today
- `static/js/script.js` lines 172-186 (commit `7d26e69` "Track Call, WhatsApp and email link
  clicks in Google Analytics", about 8 Nov 2026) sends:
  - `call_click` for `tel:` links,
  - `whatsapp_click` for `wa.me` / `whatsapp.com` links,
  - `email_click` for `mailto:` links,
  each with `link_text` (up to 50 characters of the link's text, e.g. our own phone number or
  "WhatsApp us"). GA4 adds the page address to every event automatically, so "which page" is
  already recorded.
- **There is no event for a successful enquiry.** `static/js/enquiry.js` (full form,
  `/enquiry/`) and `static/js/contact.js` (quick form in the contact section) send to
  FormSubmit and then go to `/enquiry/thank-you/`. Today an enquiry can only be guessed from:
  - GA4's automatic `form_submit`, which fires when Submit is pressed, **including sends that
    then fail**, and
  - page views of `/enquiry/thank-you/`, which also count reloads and Back-button visits.
- Because `script.js` also runs on the admin pages, admin clicks and page views (titles like
  "Edit products | AR Cooling Solutions") go to Google too.

### The mismatch
`templates/privacy.html` line 48 says: "This website does not use advertising or tracking
cookies, and has no analytics." That is not true while the tag loads. The live page
(https://arcooling.in/privacy/, "Last updated 16 November 2026") says the same. The date
comes from `PRIVACY_UPDATED` in `app.py`.

### History
- I could not run `git log -S "GTM-WZFNQQXC"` (no shell in this role). The local reflog shows
  that the event tracking in `script.js` was added in `7d26e69` (owner's commit, about 8 Nov
  2026), straight after `cba5aee` "Add home page counters, reviews, FAQ and site-wide share
  tags". The tag snippet itself was probably added in one of these two commits or just
  before. **Architect: please confirm with `git log -S "GTM-WZFNQQXC" --oneline`.**
- The tag was already noted as backlog N2 in
  `docs/work/2026-11-16-hvac-website-research/01-requirements.md`. The quick-enquiry tests
  blocked Google during testing so that test visits were not counted.

### Also true today (affects both options)
- The GitHub Pages static copy (`tools/build_static.py`) is built from the same templates, so
  it carries the tag too. Anyone visiting the old github.io address is counted under the
  same GA4 property.

---

## Requirements: shared by both options
- **S1.** Nothing about visitors is stored on our server, and no new server-side logging,
  database tables or cookies are set by our own code.
- **S2.** No new paid services. No new Python packages or background work on the 1 GB server.
- **S3.** Public page URLs, `/go/<id>/` share pages, sitemap and robots stay exactly as they
  are.
- **S4.** The admin pages (`/admin/login`, `/admin`, edit pages) load **no** Google tag and
  send nothing to Google Analytics or Tag Manager. Google Fonts may stay.
- **S5.** The privacy page's "Last updated" date changes to the release date, and every
  sentence about cookies, analytics and Google matches what the site really does.
- **S6.** `tools/check_site.py` and `tools/build_static.py` keep passing. `check_site.py`
  gains an automated check that the admin pages contain no `googletagmanager.com` /
  `gtag(` / `dataLayer` (and, in `--live` mode, that `/admin/login` on the live site has none).
- **S7.** The enquiry forms, call and WhatsApp links work exactly as before, including when
  Google scripts are blocked (ad blockers, slow networks) and without JavaScript.

---

## Option A (proposed default): keep measurement, make it honest and useful

### Requirements
- **A1. Tag on public pages only.** All public pages (everything built on `base.html`) keep
  loading GA4 through GTM-WZFNQQXC, once per page. Admin pages have none (S4).
- **A2. Call taps.** Every tap on a `tel:` link on any public page sends one event named
  `call_click`. The existing name is kept so past data stays comparable.
- **A3. WhatsApp taps.** Every tap on a WhatsApp link (`wa.me` / `whatsapp.com`) sends one
  `whatsapp_click`. `email_click` may stay as it is.
- **A4. Successful enquiries.** When FormSubmit confirms an enquiry was sent (the same
  "success" check that sends the visitor to the thank-you page), one event is sent before
  the page moves on. It is named for example `enquiry_sent`; the architect picks the final
  name. It says which form was used (full enquiry form or quick contact form) and the
  enquiry type (product / service / spare / general / quick). GA4's automatic page address
  shows which page it came from.
  - A failed send, a validation error, or reloading / going Back to the thank-you page sends
    **no** `enquiry_sent`.
  - The redirect to the thank-you page must never wait more than about 1 second for Google,
    and must still happen if Google is blocked.
  - The no-JavaScript fallback (browser posts to FormSubmit directly) is not counted. That is
    acceptable and is noted in the privacy page / owner notes.
- **A5. No personal data to Google.** Events and their details never contain the visitor's
  name, mobile, email, area, message, reference number or any typed text. Allowed details:
  event name, page address (which GA4 adds itself; our page addresses hold no personal data),
  form name, enquiry type, and the link's own text (our number or label).
- **A6. Privacy page tells the truth.** The "Cookies and other services" section (or a new
  "Visitor statistics" section) says in plain English:
  - we use **Google Analytics** (run by Google) to count visits, pages viewed, and taps on
    Call, WhatsApp, email and enquiry sends, to see which pages help customers;
  - Google Analytics sets cookies on your device (`_ga`, `_ga_…`) that last up to about
    2 years. They hold a random ID, not your name or number;
  - we do not use it for advertising, and Google Signals / ad personalisation is off;
  - what you type into the enquiry form is **not** sent to Google Analytics;
  - Google may process the data outside India, with a link to Google's privacy policy and to
    "How Google uses information from sites that use our services";
  - **how to opt out:** the Google Analytics opt-out browser add-on
    (https://tools.google.com/dlpage/gaoptout), blocking or clearing cookies in the browser,
    or a private / incognito window;
  - the line "does not use advertising or tracking cookies, and has no analytics" is
    removed. The sentences about session storage and Google Fonts stay.
- **A7. Consent banner: proposed default is no banner.** The site is Indian, aimed at
  Hyderabad customers, and uses analytics only (no ads, Signals off). Proposed default: no
  cookie banner, an honest notice on the privacy page (A6), and a short link to it near the
  footer (e.g. "Privacy & cookies"). India's Digital Personal Data Protection Act 2023 and its
  Rules may affect whether consent is needed for analytics cookies; **the owner may want
  advice on this**. This document does not give legal advice. If the owner wants a banner,
  it is a separate follow-up (it would need Google consent mode and would lower the counts).
- **A8. Owner's monthly view.** The owner can open Google Analytics (phone app or web) and
  see, for a chosen month: number of visitors, `call_click`, `whatsapp_click` and
  `enquiry_sent` counts, and those three broken down by page. This needs, in GA4 admin (not
  in our code):
  - `call_click`, `whatsapp_click` and `enquiry_sent` marked as **key events**;
  - a saved report or "Exploration" (or a monthly emailed report) with those numbers by page
    path;
  - the owner having at least **Viewer** access to GA4 property `G-EYB0ZX8K90`, and ideally
    **Administrator** on both that property and GTM container GTM-WZFNQQXC so that access is
    never lost.

  The developer / deployer writes short step-by-step notes for the owner. Optional: filter
  out the owner's own visits (GA4 "internal traffic").
- **A9. Tag snippet tidy-up (architect's choice).** The current mixed snippet must keep
  working. If the architect changes it (e.g. to standard gtag.js with `G-EYB0ZX8K90`, or the
  standard GTM snippet), page views and the three events must still arrive in the same GA4
  property, and the change must be explained in 02-design.

### Acceptance criteria (Option A)
- **AC-A1.** View source of `/`, `/services/`, `/products/`, `/parts/`, `/enquiry/`,
  `/enquiry/thank-you/`, `/privacy/` and a 404 page: each has the Google tag exactly once.
- **AC-A2.** View source of `/admin/login`, `/admin` (logged in) and one edit page: no
  `googletagmanager.com`, no `gtag(`, no `dataLayer`. In browser dev tools (Network), loading
  and clicking around these pages makes **no** request to `googletagmanager.com` or
  `google-analytics.com`.
- **AC-A3.** On a phone-size window (375 px), tapping the header Call button and a Call link
  in the page body each sends a GA4 request with `en=call_click` and the right page address
  (check in Network for `collect?v=2`, or GA4 DebugView / Tag Assistant).
- **AC-A4.** Tapping the floating / contact WhatsApp link sends `en=whatsapp_click`.
- **AC-A5.** A successful send of the full enquiry form (FormSubmit answer stubbed to
  success, as in earlier test rounds) sends exactly one `enquiry_sent` with form = full form
  and the right enquiry type, then the thank-you page opens. The same with the quick contact
  form (form = quick).
- **AC-A6.** A failed send (FormSubmit blocked / error answer) shows the existing error and
  sends **no** `enquiry_sent`. Reloading the thank-you page, or Back then Forward, sends none.
- **AC-A7.** With Google domains blocked, the Call / WhatsApp links work and a successful
  enquiry still reaches the thank-you page within 2 seconds of the success answer.
- **AC-A8.** Inspect every GA4 request made during AC-A3 to AC-A6: none contains the test
  name, mobile, email, area, message text or reference number.
- **AC-A9.** `/privacy/` no longer contains "has no analytics". It names Google Analytics,
  the `_ga` cookies and how long they last, says form contents are not sent, gives the
  opt-out options with a working link, and shows the new "Last updated" date.
- **AC-A10.** `tools/check_site.py` passes, including the new "admin pages load no Google
  tag" check. The check fails if the snippet is put back in an admin template (tester
  confirms once on a scratch copy). `tools/build_static.py` passes.
- **AC-A11.** After release, `check_site.py --live` passes, and within 48 hours the owner (or
  whoever has access) sees the test `call_click` / `whatsapp_click` / `enquiry_sent` in GA4
  Realtime or DebugView.

---

## Option B: remove all tracking

### Requirements
- **B1.** The Google tag snippet is removed from `base.html` and all three admin templates.
  No page, public or admin, and no static build page loads `googletagmanager.com`,
  `google-analytics.com` or defines `gtag` / `dataLayer`.
- **B2.** The click-tracking block in `static/js/script.js` (lines 172-186) is removed. No
  other code sends events anywhere.
- **B3.** The privacy page keeps "does not use advertising or tracking cookies, and has no
  analytics" (it is now true). The date is updated (S5).
- **B4.** `tools/check_site.py` checks that no public or admin page contains
  `googletagmanager.com` or `gtag(`.
- **B5.** The owner is told plainly that visitor, call and WhatsApp numbers stop from the
  release date. The GA4 property keeps past data until the owner deletes it there. Calls
  and enquiries can still be counted by hand (phone log, enquiry inbox, WhatsApp chats).

### Acceptance criteria (Option B)
- **AC-B1.** View source of every page in the sitemap, plus `/admin/login`, `/admin` and one
  edit page: no `googletagmanager.com`, `google-analytics.com`, `gtag(` or `dataLayer`.
- **AC-B2.** In browser dev tools, loading the home page, tapping Call / WhatsApp and sending
  a (stubbed) enquiry makes no request to any Google Analytics / Tag Manager address. Google
  Fonts requests are expected.
- **AC-B3.** After visiting the site in a fresh browser profile, there are no `_ga` /
  `_ga_*` cookies for arcooling.in.
- **AC-B4.** Call, WhatsApp and both enquiry forms work as before (S7).
- **AC-B5.** `/privacy/` still says "has no analytics" and shows the new date.
- **AC-B6.** `tools/check_site.py` (with the new check) and `tools/build_static.py` pass.
  After release, `check_site.py --live` passes.

---

## Out of scope
- A cookie consent banner or consent-mode setup (follow-up if the owner wants it, A7).
- Google Ads, Facebook pixel, call-tracking numbers, heatmaps or any other vendor.
- Changing the GA4 / GTM settings in Google's own admin screens, beyond writing the owner's
  step-by-step notes (A8). Only someone with access can do that.
- Counting enquiries sent without JavaScript, and counting WhatsApp chats that really
  started (we can only count taps).
- Tracking on the `/go/<id>/` share pages (visits are counted on the page they redirect to).
- Legal review of the privacy policy.

## Risks
- **Access risk (Option A):** if nobody on our side has access to GTM-WZFNQQXC / GA4
  G-EYB0ZX8K90 (e.g. a past helper set it up), the owner cannot see the numbers and the
  measurement is useless. Confirm access before building A8.
- **Counts are approximate:** ad blockers and some browsers block Google Analytics, so the
  numbers are a floor, not a total. Owner notes should say so.
- **Thank-you redirect:** sending the enquiry event must not slow down or break the move to
  the thank-you page (A4, AC-A7).
- **Personal data leaks:** a careless change could put form text into an event or page
  address. AC-A8 guards this.
- **Legal / regulatory:** DPDP Act 2023 obligations for analytics cookies are not settled
  here. The owner may want advice.
- **Data continuity:** keeping the event names `call_click` / `whatsapp_click` keeps history
  comparable. Renaming would split the reports.
- **Static copy:** the GitHub Pages build follows the same templates, so it changes too.
  That is expected.
- **Live site:** merging to `main` goes live within about 5 minutes. The privacy page wording
  should be approved by the owner before merge.
- **1 GB server:** no impact. All changes are templates / browser scripts.

## Open questions
1. **Option A or Option B?** Default: **Option A** (keep measurement, make it honest, add the
   enquiry count, remove it from admin pages).
2. **Who set up Google Tag Manager GTM-WZFNQQXC and Google Analytics G-EYB0ZX8K90, and can
   you (the owner) log in to both with your own Google account?** Default: assume the owner
   set it up with their own Google account (the tracking code was added from the owner's
   git account around 8 Nov 2026). If not, the person who did must add the owner as
   Administrator before we rely on the reports.
3. **Cookie banner?** Default: **no banner**, with an honest privacy notice and opt-out
   instructions. The owner may want advice on the DPDP Act 2023 before deciding.
4. **Keep counting email-link taps (`email_click`)?** Default: yes, it costs nothing and is
   already there.

## Owner decisions (2026-11-17)
- **Option A** chosen: keep Google Analytics (GTM-WZFNQQXC → GA4 G-EYB0ZX8K90), make it honest and
  useful. Option B is not built.
- **Access**: the owner set up both Tag Manager and Google Analytics and can log in with their own
  Google account.
- **No cookie banner**: honest privacy page with opt-out instructions (DPDP Act mentioned only as
  "you may want advice").
- **Q4 = default**: keep counting email-link taps (`email_click`).
- Coordinator note: `git log -S "GTM-WZFNQQXC"` shows the tag was added in cba5aee (2026-11-07,
  the owner's account, "Add home page counters, reviews, FAQ and site-wide share tags").
