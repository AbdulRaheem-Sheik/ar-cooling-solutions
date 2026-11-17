# Design: Count calls, WhatsApp taps and enquiries, and fix the privacy mismatch (Option A)

## Approach
Keep Google Analytics exactly as it loads today on public pages (the GTM-WZFNQQXC snippet in
`base.html`, unchanged), and take it out of the three admin templates together with
`script.js`, which has no job on admin pages. Then nothing on an admin page can talk to
Google. Keep the existing `call_click` / `whatsapp_click` / `email_click` code as it is. Add
one new event, `enquiry_sent`. It fires in `enquiry.js` and `contact.js` only after
FormSubmit says the send worked. Its two details come from a fixed list (`enquiry_form`,
`enquiry_type`). A small "count, then go" helper sends the visitor to the thank-you page as
soon as Google confirms, after 1 second at most, or straight away if the Google tag never
loaded. The privacy page gets a plain-English "Visitor statistics (Google Analytics)"
section and a new date. `check_site.py` gets checks that admin pages have no Google tag and
public pages have it exactly once (local and `--live`). Everything else (GA4 key events,
custom dimensions, retention) is set by the owner in Google's own screens. The design lists
those steps; they are not code.

It is the smallest change that meets A1–A9 and S1–S7. It touches only templates, two
browser scripts, one constant in `app.py` and the check script. No new packages, no server
work, no URL changes.

## Alternatives considered
- **Swap the snippet for the standard gtag.js (`gtag/js?id=G-EYB0ZX8K90` + `gtag('config')`)
  or the standard GTM snippet (A9).** Rejected for now. The current mixed snippet loads the
  container the owner set up, and the container holds the settings (Signals off, enhanced
  measurement, redaction). Changing the loader could double-count page views or drop
  container settings, and it doesn't help any requirement. Kept as a fallback, see Risks.
- **Keep `script.js` on admin pages and rely on its `typeof gtag !== 'function'` guard.**
  This works once the snippet is gone, but it leaves analytics code on admin pages that a
  later edit could wake up again. Admin pages use nothing in `script.js`: no `.menu-toggle`,
  `.reveal`, `#year`, carousel, counters or `data-nav-item` (checked by grep). Removing it
  is simpler and safer.
- **A Jinja flag or partial (`_google_tag.html`) included conditionally.** Not needed. After
  the change only `base.html` has the snippet, and admin templates don't extend `base.html`.
- **`dataLayer.push({event: 'enquiry_sent'})` plus a GA4 Event tag built in GTM.** This
  needs the owner to configure GTM, and the existing events already use `gtag('event')`.
  Rejected unless the gtag path turns out not to reach GA4 (Risks).
- **One shared helper in `script.js` for both forms.** `enquiry.js` and `contact.js` would
  then depend on script load order and on a global. Each form file already carries its own
  copy of small helpers (`makeReference`), so a 10-line copy in each, with a comment pointing
  to its twin, keeps each form self-contained.

## Changes by file

### `templates/admin_login.html`, `templates/admin_dashboard.html`, `templates/admin_edit.html`
- Delete lines 4–11 in each: the `<!-- Google tag -->` comment, both snippet `<script>`
  tags and the `<script src=".../js/script.js" defer>` line. Nothing else changes; Google
  Fonts and `style.css` stay.

### `templates/base.html`
- The snippet stays byte-for-byte (A1, A9). Only the comment changes, to explain why, e.g.
  `<!-- Google Analytics (via Tag Manager GTM-WZFNQQXC). Public pages only: admin templates
  must not load it (checked by tools/check_site.py). Explained on /privacy/. -->`
- Footer: link text `Privacy policy` becomes `Privacy & cookies` (A7: "short link near the
  footer"). Same `url_for('privacy')`, same URL. (See Questions 2.)

### `static/js/script.js`
- No change in behaviour. Only update the comment above the click tracker: say that only
  public pages load this file with the Google tag, and that `link_text` is the link's own
  text (our number or label), never anything the visitor typed (A5).

### `static/js/enquiry.js` (full form, `/enquiry/`)
- Add a helper inside the IIFE (the same text goes in `contact.js`):
  ```js
  // Count the sent enquiry in Google Analytics, then open the thank-you page. Waits for
  // Google at most 1 second, and not at all if the Google tag didn't load (blocked, slow).
  // Only fixed words are sent, never what the visitor typed. Twin: contact.js.
  function countEnquiryThenGo(url, details) {
    let gone = false;
    const go = () => { if (!gone) { gone = true; window.location.href = url; } };
    if (typeof gtag !== "function" || !window.google_tag_manager) return go();
    gtag("event", "enquiry_sent", { ...details, event_callback: go, event_timeout: 1000 });
    setTimeout(go, 1000);
  }
  ```
  `window.google_tag_manager` is the global that `gtm.js` creates when it has loaded. If it
  is missing, nobody would process the event before the page moves on, so we go at once.
  The `setTimeout` is the real guarantee: it works even if `event_callback` is never called
  through the container (AC-A7).
- In the submit handler, after the `sessionStorage` block, replace
  `window.location.href = data.thanksUrl;` with
  `countEnquiryThenGo(data.thanksUrl, { enquiry_form: "full", enquiry_type: safeType });`
  where `safeType` is `enquiryType()` limited to `product | service | spare | general`
  (anything else becomes `general`). A wrong value then can never carry text.
- The failure path (`catch` → `showError` → `return`) and validation (`reportValidity`) are
  untouched, so they send nothing (AC-A6).

### `static/js/contact.js` (quick form, contact section)
- The same helper. Replace `window.location.href = form.dataset.thanksUrl;` with
  `countEnquiryThenGo(form.dataset.thanksUrl, { enquiry_form: "quick", enquiry_type: typeKeys[topic] || "general" });`
  `topic` comes from the form's own fixed `<select>` choices, mapped through `typeKeys`, so
  only the four fixed words can be sent.

### Event definition (for developer, tester and owner notes)
| Event | Fired when | Details sent | Notes |
|---|---|---|---|
| `call_click` | tap on any `tel:` link (public pages) | `link_text` | unchanged |
| `whatsapp_click` | tap on a `wa.me` / `whatsapp.com` link | `link_text` | unchanged |
| `email_click` | tap on a `mailto:` link | `link_text` | unchanged (owner's choice, Q4) |
| `enquiry_sent` **(new)** | FormSubmit answered success, just before the thank-you page | `enquiry_form` = `full` \| `quick`; `enquiry_type` = `product` \| `service` \| `spare` \| `general` | never on failure, validation error, thank-you reload or Back/Forward |

GA4 adds the page address (`page_location`) itself. Our page addresses carry no personal
data. Enquire-link query strings such as `?product=…&comments=…` hold only our own text,
built in `app.py` lines ~515–540.

### `templates/privacy.html`
- "What we collect": change the opening line to "Through the enquiry form we only collect
  what you choose to send us:" (the current "We only collect what you choose to send" stops
  being true). Keep the list. After "Browsing the site does not require you to give us any
  personal information." add "We do count visits, as explained under *Visitor statistics*
  below."
- New section **"Visitor statistics (Google Analytics)"** before "Cookies and other
  services". Draft wording, to be approved by the owner before merge:
  > We use **Google Analytics**, a service run by Google, to count how many people visit
  > this website, which pages they look at, and how many tap Call, WhatsApp or email or send
  > an enquiry. This tells us which pages help customers reach us.
  > - Google Analytics stores two cookies on your device, `_ga` and `_ga_EYB0ZX8K90`. They
  >   hold a random number so a return visit can be told apart from a new one, not your
  >   name or phone number. They last up to 2 years unless you clear them.
  > - Google receives the page address, your type of device and browser, and your rough
  >   location (city or region). Google says Google Analytics does not store IP addresses:
  >   it uses your IP address only briefly to estimate that location.
  > - **What you type into the enquiry form is not sent to Google Analytics.** We only
  >   record which form was used and the kind of enquiry (product, service, spare part or
  >   general).
  > - We do not use Google Analytics for advertising. Google Signals and ad
  >   personalisation are turned off. We see totals and reports, not who you are.
  > - Google handles this data for us and may process it outside India. See
  >   [Google's privacy policy](https://policies.google.com/privacy) and
  >   [How Google uses information from sites or apps that use our services](https://policies.google.com/technologies/partner-sites).
  > - **To opt out:** install the
  >   [Google Analytics opt-out browser add-on](https://tools.google.com/dlpage/gaoptout),
  >   block or clear cookies for this site in your browser settings, or use a private /
  >   incognito window. The website works the same either way.
  > - *(Only if the owner sets retention, see owner step 4:)* Google Analytics keeps the
  >   detailed statistics for 14 months.
- "Cookies and other services": delete the "does not use advertising or tracking cookies,
  and has no analytics" item. Add instead: "The only cookies are the Google Analytics ones
  described above. We don't use advertising cookies." Keep the session-storage and Google
  Fonts items word for word.
- All external links use `target="_blank" rel="noopener noreferrer"`, like the existing ones.

### `app.py`
- `PRIVACY_UPDATED = "<release date>"`, e.g. `"17 November 2026"`. The developer sets the
  expected date; if the merge slips, the deployer updates it on the branch before merge
  (S5). No other change.

### `tools/check_site.py`
- Constants:
  ```python
  GOOGLE_TAG = "googletagmanager.com/gtm.js?id=GTM-WZFNQQXC"
  # Anything that would make an admin page talk to Google Analytics / Tag Manager.
  TRACKING_MARKERS = ("googletagmanager.com", "google-analytics.com", "gtag(", "dataLayer")
  ```
- Helpers: `tag_count(html) -> html.count(GOOGLE_TAG)` and
  `tracking_found(html) -> [m for m in TRACKING_MARKERS if m in html]`.
- `check_pages`: in the existing loop, also collect pages where `tag_count != 1`, plus the
  404 response. New line: `check(not bad, "public pages load the Google tag exactly once")`.
- `check_admin`: run `tracking_found` on the `/admin/login` page (already fetched for the
  token), the dashboard and the edit page. New line:
  `check(not found, "admin pages load no Google tag", "<page>: <markers>")`.
- New consistency check (cheap, protects S5 from drifting): `/privacy/` contains
  "Google Analytics" and does not contain "has no analytics" while `GOOGLE_TAG` is on public
  pages.
- `check_live`: `/` and `/admin/login` are already in `files`. Add
  `check(tag_count(home) == 1, "live home page loads the Google tag once")` and
  `check(not tracking_found(login), "live /admin/login loads no Google tag")`.
  (The live dashboard needs a login, and `--live` must not use the real password. The local
  check covers dashboard and edit, which use the same templates.)
- Update the module docstring's list of checks.

### Not changed
`templates/_contact.html`, `product_enquiry.html`, `enquiry_thanks.html`, `store.py`,
`data/`, `tools/build_static.py`, `deploy/`, `serve.py`, CSS.

## Data & migration
None. No database, `data/*.json` or `posts.json` change. No server-side storage, logging or
cookies from our code (S1). Static file URLs carry a content hash (`app.py` ~line 409), so
browsers pick up the new `enquiry.js` / `contact.js` straight away.

## URLs & SEO
- No new, changed or removed URLs. `/go/<id>/`, sitemap, robots and canonical tags are
  unchanged (S3). The privacy page keeps `/privacy/`, and only its text changes.
- Structured data is unchanged. The footer link keeps its address; only its words change.
- The GitHub Pages copy keeps the tag on public pages (as today) and gets the new privacy
  text. Admin pages are not part of the static build.

## Deployment notes
- Code: merging to `main` is the release (about 5 minutes). No `setup.sh`, no restart beyond
  the automatic one, no live database step.
- **Before merge:** the owner approves the privacy wording, and `PRIVACY_UPDATED` matches
  the merge date.
- **Owner steps in Google's screens (not code).** The developer/deployer turns these into
  short step-by-step notes (A8):
  0. *Check that events already arrive:* GA4 → Reports → Engagement → Events. `call_click`
     / `whatsapp_click` should show counts since about 8 Nov 2026. This proves that
     `gtag('event')` calls reach GA4 through the GTM container. If they are missing, tell
     the team before release (see Risks).
  1. GA4 → Admin → Events / Key events: mark `call_click`, `whatsapp_click` and (once it
     has appeared, or create it as a new key event by name) `enquiry_sent` as **key
     events**.
  2. GA4 → Admin → Custom definitions: add event-scoped custom dimensions `enquiry_form`,
     `enquiry_type` and (optional) `link_text`. Without them the details are collected but
     can't be shown in reports. They start counting from the day they are created.
  3. A saved Exploration (or Library report) for "month, page path × event count" of the
     three key events, plus Users. Optionally a monthly scheduled email.
  4. GA4 → Admin → Data collection and modification → Data retention: set event data
     retention to **14 months** (the default is 2 months, which limits Explorations for
     monthly comparisons). If done, keep the 14-month sentence on the privacy page.
  5. Confirm GA4 → Admin → Data collection: **Google Signals stays off**. Leave "granular
     location and device data" at its default. The privacy page says Signals is off, so
     this must stay true.
  6. Optional: GA4 → Admin → Data streams → Configure tag settings → Define internal
     traffic, to exclude the owner's own visits.
  7. Access: the owner is already Administrator on both (owner decision). Adding a second
     trusted Google account as Administrator is recommended so access is never lost.
  8. GTM (tagmanager.google.com → container GTM-WZFNQQXC → Tags): confirm the container
     only has the Google tag / GA4 tags (no Ads, Floodlight, other vendors), and that
     Admin → Container settings has no consent overview requiring a banner. I could not
     fetch the remaining ~447 KB of `gtm.js` in this role (no network tool). This screen is
     the reliable check, and AC-A2/A3 Network checks back it up.
- Tell the owner (owner notes): the counts are a floor (ad blockers, opt-outs), and
  enquiries sent with JavaScript switched off are not counted. Use `enquiry_sent`, not
  GA4's automatic `form_submit`, which also counts failed sends. DPDP Act 2023: the owner
  may want advice on consent for analytics cookies. This design does not give legal advice.

## Test plan
| AC | How |
|---|---|
| AC-A1 | `check_site.py` new check (all `page_paths` + 404 have `GOOGLE_TAG` exactly once). Tester also opens view-source on `/`, `/services/`, `/products/`, `/parts/`, `/enquiry/`, `/enquiry/thank-you/`, `/privacy/` and a 404. |
| AC-A2 | `check_site.py` admin check (login, dashboard, edit). Manually: dev tools Network, filter `google`, load `/admin/login`, log in, open the dashboard and an edit page, click around. Expect no `googletagmanager.com` / `google-analytics.com` requests; only `fonts.googleapis.com` / `fonts.gstatic.com`. |
| AC-A3 | 375 px window, Google not blocked, Network filtered `collect?v=2`. Tap header "Call us" and a body Call link: each gives `en=call_click` with the right `dl=` page address. Or GA4 DebugView with Tag Assistant. |
| AC-A4 | Tap the floating / bottom-bar WhatsApp link: `en=whatsapp_click`. |
| AC-A5 | Stub FormSubmit success (as in earlier rounds, e.g. dev tools request override or a local stub of the endpoint). Full form with `?service=…`: exactly one `en=enquiry_sent` with `ep.enquiry_form=full` and `ep.enquiry_type=service`, then the thank-you page. Quick form with topic "Spare part": `enquiry_form=quick`, `enquiry_type=spare`. Also a general full-form case. |
| AC-A6 | Stub a FormSubmit error / block it: error message shown, no `enquiry_sent`. Submit with an empty required field: none. On the thank-you page: reload, Back then Forward: none. |
| AC-A7 | Block `googletagmanager.com` and `google-analytics.com` (dev tools request blocking). Call/WhatsApp links open as normal. Stubbed successful send reaches the thank-you page at once (no `google_tag_manager`). Also with only `google-analytics.com` blocked (GTM loads, the hit can't be sent): redirect within about 1 s. Time it from the success response in the Network/Performance panel; it must be under 2 s. |
| AC-A8 | Use distinctive test values (name "Zqtest", mobile 9000000001, email, area, message, reference shown on thank-you). Search the payloads of every `collect` request during A3–A6 for each value: no hits. |
| AC-A9 | `/privacy/`: no "has no analytics"; mentions Google Analytics, `_ga` / `_ga_EYB0ZX8K90`, "2 years", that form contents are not sent, the opt-out add-on link (opens), cookie / private-window options, new date. `check_site.py` consistency check. |
| AC-A10 | `check_site.py` passes. On a scratch copy, paste the snippet back into `admin_login.html` → the admin check FAILS. Revert. `build_static.py` passes. |
| AC-A11 | After release: `check_site.py --live` (includes the live home tag-once and live `/admin/login` no-tag checks). Owner/tester sees the test events in GA4 Realtime / DebugView within 48 h. |
| S7 / no-JS | With JavaScript off, both forms still post straight to FormSubmit as before (nothing changed on that path). |

## Risks & mitigations
- **gtag events might not reach GA4 through the GTM container.** `gtag('event')` pushes to
  `dataLayer`. The GA4 Google tag inside a GTM container processes these commands, but this
  depends on the container's set-up, which I could not fully read. *Mitigation:* owner step
  0 (existing `call_click` counts prove the path) and the AC-A3 Network check before
  relying on `enquiry_sent`. *Fallback, if they don't arrive:* add the standard gtag.js
  loader for `G-EYB0ZX8K90` alongside or instead of the container (A9), and check page views
  are not doubled. This would be a design change; come back to the architect.
- **`event_callback` may not fire through GTM.** The 1-second `setTimeout` always sends the
  visitor on, and `gone` stops a double redirect. Worst case: a 1 s pause on a successful
  send when GTM loaded but the hit is slow or blocked.
- **Event lost if the visitor's GTM hadn't loaded yet** (very slow network). We go at once
  and that enquiry is not counted. This is acceptable because counts are a floor.
- **Personal data leaking into events.** Only fixed words are sent, with the type checked
  against a fixed list. AC-A8 searches the payloads. GA4's automatic `form_start` /
  `form_submit` send the form id/name/destination, not field values, and the destination
  is our own FormSubmit address.
- **Admin tag creeping back.** The new local and live checks fail if any marker reappears.
- **Privacy text going stale** (e.g. the owner turns on Signals or adds an Ads tag in GTM).
  The owner notes say: tell the team before changing Google settings. The consistency check
  catches the tag/privacy-page mismatch in our code, but not changes made in Google's
  screens.
- **Legal:** no banner by owner decision. DPDP advice is flagged to the owner, not settled.
- **Server:** no impact (templates and browser scripts only).

## Questions for requirements
1. **`enquiry_type` for the quick form.** A4 lists "quick" as a type. I recommend sending
   the topic the visitor picked (`product` / `service` / `spare` / `general`) as
   `enquiry_type`, and `enquiry_form=quick` to show it was the quick form. That gives more
   useful reports, and "quick" is still visible. Recommended answer: accept.
2. **Footer link text "Privacy & cookies".** A7 suggests it. Same URL, only the words
   change. Recommended answer: accept. If the owner prefers, keep "Privacy policy".
3. **14-month retention sentence.** Include it only if the owner changes GA4 retention
   (owner step 4) before release. Recommended answer: owner sets 14 months, and the
   sentence stays.

## Coordinator decisions and findings (2026-11-17)
- **Full container checked** (coordinator fetched all 547,116 bytes of gtm.js?id=GTM-WZFNQQXC):
  the only measurement ID is G-EYB0ZX8K90 (18 references); no AW-/UA-/DC-/GT- IDs; the only
  third-party domain is facebook.com inside GTM's built-in form listener that *skips*
  facebook.com/tr forms (no Meta pixel: no fbq / connect.facebook.net / fbevents). The consent
  strings are generic library code; no consent configuration was found. Owner step 8 stays as a
  belt-and-braces check.
- Questions for requirements: 1 accepted (quick form topic as `enquiry_type`, `enquiry_form=quick`);
  2 accepted (footer link text "Privacy & cookies", URL unchanged); 3 accepted (owner sets GA4 data
  retention to 14 months; the privacy sentence stays — this owner step is required before merge).
- **Owner step 0 done (2026-11-17)**: the owner sees `call_click` / `whatsapp_click` in GA4 Reports → Engagement → Events, so `gtag()` events reach GA4 through the container; the fallback loader is not needed.
