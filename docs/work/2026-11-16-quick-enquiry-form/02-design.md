# Design: Quicker enquiry form for home customers (backlog N1)

## Approach
This is a front-end-only change: two templates, two scripts, one stylesheet, and the privacy
page with its date. No new routes, packages, database fields or server work.

1. **/enquiry/ form** (`templates/product_enquiry.html`). Put the fields in the R10 order.
   Only name, mobile and category keep `required`. Add an optional **Area / locality** text
   field and an optional **Preferred visit time** `<fieldset>` with three controls: a *Day*
   select, a *Date* input (used for "Pick a date") and a *Time of day* select. The choices are
   exactly the owner's list. Options use readable text as their `value`, so the no-JavaScript
   email is readable too.
2. **Making an empty email safe.** FormSubmit treats `_replyto` *and* a field called `email` as
   the Reply-To address, so neither should ever arrive empty or as "Not given":
   - JavaScript path: send `_replyto` **only when an email was typed**. The table row is
     labelled **"Email address"** (not `Email`/`email`), so FormSubmit can never take
     "Not given" for an address.
   - No-JavaScript path: rename the input from `name="email"` to `name="email_address"`. The
     browser always posts every field, even empty ones, so this is the only way an empty email
     can never reach FormSubmit as `email=`. The trade-off: a no-JavaScript visitor who *does*
     give an email loses one-click Reply, but the address is still in the email. The same
     applies to the contact-section form.
3. **The email table** is built in `emailPayload()` in the R15 order. One helper,
   `orNotGiven(v)`, fills empty optional fields with "Not given" (Comments keeps "None").
   A new `visitTimeText()` turns day + date + time into one line. The subject, reference,
   type labels, routing, prefill, the "You're enquiring about" card and session storage
   don't change.
4. **CSS fix.** The red colour moves from `.form-field label > span:first-child` to an explicit
   class `.required-mark`, so the grey "Optional" tag can never turn red again.
5. **Contact-section form**: email becomes optional with the same rules, and the wording is
   updated. Nothing else changes there.
6. **Privacy page**: update the "What we collect" list and `PRIVACY_UPDATED`.

## Alternatives considered
- **Keep `name="email"` on the no-JS form and rely on a test send.** Rejected: FormSubmit
  doesn't document what an empty `email` does, and the no-JS path can't drop an empty field.
  Renaming removes the risk for good, at a small cost on a rarely used path.
- **Let JavaScript rename the field back to `email` when it runs.** Pointless: the JavaScript
  path builds its own JSON and never uses the input names.
- **A free date picker only (no Today/Tomorrow).** Rejected: slower on phones. The owner chose
  the select plus "Pick a date".
- **Server-rendered `min`/`max` on the date input.** Rejected: the GitHub Pages build would
  freeze the dates at build time, and a stale `max` would block valid dates. The browser
  works the limits out instead (see below).
- **Custom JavaScript error messages for every field.** Not needed: R26 accepts the browser's
  own checks (`reportValidity()` names the field, focuses it and is announced). Only the
  "Pick a date with no date" case gets a custom message.
- **A check in `tools/check_site.py` that only the 3 fields are required.** Left out to keep
  the change small. The tester checks it by hand (AC1, AC6). This can be added later.

## Changes by file

### `templates/product_enquiry.html`
- **Field order inside `.form-grid`** (on desktop it is 2 columns; at 600px and below it is
  1 column in this order):
  1. Full name (half) · 2. Mobile number (half). Both stay `required`. Mobile keeps
     `type="tel" inputmode="tel" pattern title maxlength` exactly as today.
  3. Enquiry category (full, `required`, the same live category loops).
  4. Product / service details (full, **no `required`**, `<span class="optional-label">Optional</span>`).
     New placeholder: "AC brand/model, capacity, quantity, or the problem you're seeing".
     It no longer mentions area or time.
  5. Area / locality (full): `<input id="area" name="area" type="text"
     autocomplete="address-level3" maxlength="120" placeholder="e.g. Kukatpally, Banjara Hills">`, Optional.
  6. Preferred visit time (full): a `<fieldset class="form-field form-field-full visit-time"
     aria-describedby="visit-time-note">` with `<legend>Preferred visit time <span
     class="optional-label">Optional</span></legend>`. Inside it is a nested `<div
     class="form-grid">`, so it stacks on phones with no extra CSS:
     - `<label for="visit-day">Day</label>` `<select id="visit-day" name="visit_day">`. Options
       (value = text): **No preference** (selected) / **Today** / **Tomorrow** / **Pick a date**.
     - `<label for="visit-time">Time of day</label>` `<select id="visit-time" name="visit_time">`:
       **Any time** (selected) / **Morning (9am–12pm)** / **Afternoon (12pm–4pm)** /
       **Evening (4pm–7pm)**.
     - A wrapper `<div class="form-field form-field-full" data-visit-date>` containing
       `<label for="visit-date">Date <span class="optional-label">if you chose "Pick a
       date"</span></label>` and `<input id="visit-date" name="visit_date" type="date">`.
       It is visible in the HTML (so it works without JavaScript, R19). JavaScript hides it
       until "Pick a date" is chosen.
     - `<p class="form-hint" id="visit-time-note">We're open Mon–Sat, 9am–7pm. We'll call you to
       confirm the time.</p>` (R8)
  7. Email address (half): `id="email" name="email_address" type="email"`, **no
     `required`**, Optional.
  8. Company name (half): label "Company name (if it's for a business)", **no `required`**,
     Optional.
  9. Comments (full): unchanged, Optional.
- Required labels use `<span class="required-mark" aria-hidden="true">*</span>`.
- **Service side panel** (R12): change "Your area and preferred visit time" to "When suits you:
  pick a day and time in the form". The default panel, hero, card and call button stay as they are.
- **Submit-row text** (R13): "Your enquiry is emailed to our team. We'll call you back on your
  mobile (or reply by email if you give one). See our privacy policy."
- The hidden inputs (`_subject`, `_template`, `_captcha`, `_next`, `reference`, …, `_honey`) stay
  as they are. No hidden `_replyto` input is added.

### `static/js/enquiry.js`
- **Prefill, `enquiryType()`, `showVariant()`, the card and `makeReference()`: no change.** The
  code finds everything by name or id, so moving fields around in the page doesn't affect it.
- **Rename the field it reads**: `field("email")` becomes `field("email_address")` (the input id stays `email`).
- **New "visit date" section** (about 30 lines):
  - `isoLocal(date)` builds `YYYY-MM-DD` from `getFullYear/getMonth/getDate`. **Don't use
    `toISOString()`**: it uses UTC, and in India (UTC+5:30) it gives yesterday's date between
    midnight and 5:30am.
  - On load, set `visit_date.min = isoLocal(today)` and `max = isoLocal(today + 30 days)`
    (AC10). Sundays stay selectable (owner decision).
  - `syncVisitDate()`: when the day is "Pick a date", show the date wrapper and make the date
    `required`. Otherwise hide it, remove `required` and **clear its value**. A hidden field
    that is required or out of range would block the form with "invalid form control is not
    focusable". Run it on load, on `change` of the day select, and on `pageshow` (the browser
    may restore the old choice when the visitor comes back).
  - If the date input changes to a value, set the day select to "Pick a date".
  - Custom message for an empty required date: `setCustomValidity("Choose a date, or pick
    another day option.")`. Clear it on `input`/`change`. Past dates and dates more than
    30 days ahead use the browser's own min/max message.
- **`visitTimeText()`** gives one row (R14):
  - Day "No preference" and time "Any time" → "Not given" (AC1).
  - Today/Tomorrow get the real date added, because the team may read the email later:
    "Tomorrow (Tue 17 Nov), Morning (9am–12pm)".
  - Pick a date → "Tue 18 Nov 2026, Afternoon (12pm–4pm)". Build the date with
    `new Date(y, m-1, d)` (local time) and format it with `toLocaleDateString("en-IN",
    {weekday:"short", day:"numeric", month:"short"[, year:"numeric"]})`.
  - A day with any time → "Tomorrow (Tue 17 Nov), any time". Any day with a time → "Any day,
    Morning (9am–12pm)".
  - The tester should agree this wording matches AC4's "Tomorrow, Morning (9am–12pm)". It
    adds the date in brackets, which the requirement allows ("or the agreed wording").
- **`emailPayload()`** is rebuilt in the R15 order:
  ```js
  const email = value("email_address");
  const payload = { _subject, _template: "table", _captcha: "false", _honey,
    "Reference", "Enquiry type", "Enquiring about", "Name", "Mobile",
    "Area / locality": orNotGiven(value("area")),
    "Preferred visit time": visitTimeText(),
    "Category", "Details": orNotGiven(value("details")),
    "Comments": value("comments") || "None",
    "Email address": orNotGiven(email),
    "Company": orNotGiven(value("company")),
    "Page": value("page_link") || "Enquiry form" };
  if (email) payload._replyto = email;   // never send an empty or "Not given" Reply-To
  ```
  (`_` keys don't appear in the table, so where `_replyto` sits in the object doesn't matter.
  The order of the visible rows stays as above.)
- Submit, subject, endpoint choice, the error message and session storage
  (`name, about, type, reference` only, R21) stay as they are.

### `templates/_contact.html`
- Email: `name="email_address"`, no `required`, label "Email address <span
  class="optional-label">Optional</span>". Required labels use `.required-mark`.
- Submit-row text matches R13 (same sentence as /enquiry/).
- The message placeholder stays (there's no area field here, so "your area" there is still right).
- No other fields change (R23).

### `static/js/contact.js`
- Read `value("email_address")`. Send `_replyto` only when it isn't empty. Rename the row
  `"Email"` to `"Email address": email || "Not given"`. The subject, reference, rows,
  storage and thank-you flow don't change (R24).

### `static/css/style.css`
- Line 689: `.required-note b, .form-field label > span:first-child` becomes
  `.required-note b, .required-mark`. This is the bug fix.
- Reset the fieldset and style the legend like a label: `.visit-time { margin: 0; padding: 0;
  border: 0; min-width: 0; }` and `.visit-time legend { padding: 0; margin-bottom: 8px; color:
  var(--ink); font-size: 12px; font-weight: 600; }`. The new selects/inputs automatically get
  the existing `.form-field select/input` styles (52px tall, same as the other fields, R27).
- `.form-hint { margin: 0; color: var(--muted); font-size: 11px; line-height: 1.5; }`.
- Contact-section sizes (lines 340–343) already cover the email input. Nothing new is needed.

### `templates/privacy.html` + `app.py`
- "What we collect" list (R28):
  - "your name and mobile number;"
  - "if you choose to give them: your email address, company name, area / locality and
    preferred visit time;"
  - "the product, service or spare part you're asking about, and any details or comments you add."
- `PRIVACY_UPDATED` changes to the release date. The developer sets "16 November 2026". If the
  merge happens on a later day, the deployer or developer updates it in the same PR before merging.
- No other `app.py` changes. `fallback_action` and `contact_fallback_action` stay as they are.

### Not changed
`store.py`, `data/*.json`, `enquiry_thanks.html`, `tools/build_static.py`, `tools/check_site.py`,
`deploy/`. Static file URLs already carry `?v=<hash>` (`app.py` ~line 409). That stops an
old cached `enquiry.js` (which reads `email`) from running against the new page (where the
field is `email_address`).

## Data & migration
None. There is no change to the database or `data/*.json`. Categories still come from the live database.

## URLs & SEO
No new or changed URLs. /enquiry/ and /enquiry/thank-you/ stay as they are, and thank-you stays out
of the sitemap. `/go/<id>/` links aren't touched. The /privacy/ text changes, and its sitemap
lastmod is already "today".

## Deployment notes
Merge to `main` as normal. The server pulls it within 5 minutes, with no restart needed beyond
the usual one. No `setup.sh` step, no live database step, no new packages, and no extra memory.
Before merging, check that `PRIVACY_UPDATED` matches the actual release date.

## Test plan
Use a phone-sized viewport (375px) unless stated otherwise. Run the local dev server on the
branch (`.venv/Scripts/python app.py`).

### A. Local checks, no real sends (do all of these first)
| AC | How |
|---|---|
| AC2 | Submit with name empty, then mobile empty, then no category: each time it doesn't send, the browser message names the field, and focus moves to it. |
| AC3 | Mobile `abc` is blocked with the "Digits, spaces…" hint. Email `name@` is blocked. `+91 98765 43210` is accepted. |
| AC6 | Check the order at 375px (R10). Only the first three fields show `*`, and every other label shows grey "Optional" (look at the computed colour: `--muted`, not `--danger`). Do the same on the home page contact form for Email. |
| AC7 | The note "We'll call you to confirm the time" is under the visit time. Open `/enquiry/?service=repair&category=Repair`: the side panel and Details placeholder don't ask the visitor to type area or time. |
| AC10 | Choose Pick a date: the date field appears. Days before today are greyed out. Type yesterday's date or one 31 days ahead: blocked with a message. Choose Pick a date with no date: "Choose a date, or pick another day option." Choose No preference again: the date field hides and the form sends. Also check the min date is correct when the PC clock is set to between 00:00 and 05:30 IST (or reason from `isoLocal`). |
| AC8 (product, spare) and AC11 (with email) | In DevTools, Network, **block request URL `formsubmit.co`**. Submit from one product page's Enquire button and one spare-part page. In the Network tab, check the request payload: subject "New product enquiry: …" / "New spare part enquiry: …", the R15 row order, and the card, heading and title prefilled. Contact form with a valid email: the payload has `_replyto` set to it. Contact form with no email: no `_replyto`, and "Email address": "Not given". Blocking the request also tests **AC15**: the "couldn't be sent … call us on …" message appears and the button works again. |
| AC1/AC4 payload | With formsubmit.co still blocked, check: minimal send → `"Preferred visit time": "Not given"`, Area/Details/Email address/Company = "Not given", no `_replyto` key. Full send → "Tomorrow (…), Morning (9am–12pm)", Area "Kukatpally". |
| AC12 (storage) | After any send, session storage `ar-enquiry` has only name, about, type, reference. |
| AC13 | Keyboard only: Tab order follows R10, and the day/time/date controls work with the arrow keys and Enter. With NVDA, it reads "Preferred visit time, group" plus each label and the note. |
| AC14 | /privacy/ list and date. |
| AC16 | `tools/check_site.py` and `tools/build_static.py` pass. Check /enquiry/ and / at 320px, 375px and desktop for layout breaks, and that the visit-time selects stack at ≤600px. |
| AC9 (blocking part) | JavaScript off: an empty name is blocked by the browser. The date input is visible and usable. |

### B. Real test sends to the live inbox (owner-approved, at most 4, done once)
- **Who and when:** the **tester** only, **once**, after every check in section A passes and
  before the reviewer signs off. Tell the owner just before sending ("sending 4 labelled test
  enquiries now"). Don't repeat them in later test rounds. If a later code change affects
  what is sent, ask the owner before any extra send.
- **Labels:** Name = **"TEST – please ignore"**, Details/Message starts with **"TEST – please
  ignore"**, Mobile = the business's own number (`business.phone_display`), so no stranger
  is called. For the email in T2, use one the owner agrees to (default: `enquiry@arcooling.in`).
- **Sent from:** the branch running locally (`http://127.0.0.1:5000`).
  **Stop rule:** if FormSubmit's reply asks for activation or confirmation for this origin, or
  T1's email hasn't arrived after 10 minutes, stop. Don't click any activation link. Report it
  to the owner, who decides whether to activate it or to do the sends straight after merging
  on https://arcooling.in (the same 4 sends).

| # | Path | What is sent | Proves |
|---|---|---|---|
| T1 | JavaScript, /enquiry/ (no link parameters) | Only name, mobile and category (any category). No email. | AC1 (thank-you page shows name and reference, email has "Not given" rows), **AC5** (delivered; Reply in the inbox isn't empty or broken), AC12 (Network: the only form request goes to formsubmit.co) |
| T2 | JavaScript, /services/repair/ → Book/Enquire | All fields: Area "Kukatpally", Tomorrow, Morning, the agreed email, a company | AC4 (rows in R15 order, the visit-time line, Reply goes to the given email), AC8 (service subject and the prefill) |
| T3 | **JavaScript off**, /enquiry/ | Name, mobile, category, area, Day "Pick a date" + a date, a time. **Email left empty.** | AC9 (FormSubmit accepts it, lands on /enquiry/thank-you/, the email includes `area`, `visit_day`, `visit_date`, `visit_time`, and an empty email is accepted) |
| T4 | JavaScript, home page contact form | Name, mobile, topic, message. **No email.** | AC11 (sends, thank-you page shows the reference, "Email address: Not given") |

Write down each send's time and reference in the test report, so the owner can delete them from the inbox.

## Risks & mitigations
- **FormSubmit and an empty email.** Removed by design: JavaScript never sends an empty or
  "Not given" `_replyto`, and neither path has a field called `email`. T1, T3 and T4 confirm it.
- **No-JavaScript visitors who give an email lose one-click Reply** (because the field is
  renamed). This affects very few people, the address is still shown in the email, and the
  team calls by phone anyway. If the owner objects, see Q2.
- **Local sends may need FormSubmit activation.** Covered by the stop rule above.
- **Date limits without JavaScript:** without JavaScript the date has no min/max, because a
  server-rendered limit would go stale in the static build. The note says "we'll call to confirm", so
  a wrong date only means a phone call. AC10 is tested with JavaScript on.
- **Hidden required date blocking the form.** `syncVisitDate()` removes `required` and clears
  the value whenever the date field is hidden.
- **UTC date bug.** Use `isoLocal()` and never `toISOString()`.
- **Owner's email filters:** the subject doesn't change. Only the body rows change, including the
  "Email" row now being called "Email address".
- **Cached old script:** handled by the existing `?v=<hash>` on static file URLs.

## Questions for requirements
- **Q1. Row label "Email" → "Email address".** R15 names the row "Email". I recommend
  **"Email address"**, so FormSubmit can never mistake the row for its special `email` field
  when it says "Not given". It is a body-only change and the subject doesn't change.
- **Q2. No-JS email field renamed to `email_address`** (no Reply-To on the rare no-JS path).
  I recommend accepting it, because it's the only way an empty email can never reach FormSubmit
  as `email=` without JavaScript.
- **Q3. Visit time wording.** I recommend adding the real date for Today/Tomorrow, e.g.
  "Tomorrow (Tue 17 Nov), Morning (9am–12pm)", so an email read the next day isn't ambiguous.

## Coordinator decisions (2026-11-16)
All three "Questions for requirements" accepted as recommended (no scope change, not escalated):
1. Table row "Email" renamed "Email address". 2. No-JS input renamed `email_address`; the lost
Reply-To on the no-JS path is accepted (the address still appears in the email). 3. The real
date is shown after Today/Tomorrow in the visit-time row.
