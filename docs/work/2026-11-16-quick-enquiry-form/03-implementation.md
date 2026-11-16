# Implementation: Quicker enquiry form for home customers (backlog N1)

## Summary
On /enquiry/ only Full name, Mobile number and Enquiry category are now required, and they
come first. After them come the optional Details, a new **Area / locality** field, a new
**Preferred visit time** group (Day / Time of day / a date box for "Pick a date", plus the note
"We're open Mon–Sat, 9am–7pm. We'll call you to confirm the time."), then the optional Email,
Company and Comments. The emailed table follows the R15 row order. Empty optional fields show
"Not given" (Comments still shows "None"). `_replyto` is only sent when the visitor typed an
email address. In both forms the email input is now named `email_address`, so an empty field
called `email` can never reach FormSubmit. In the contact-section form, email is now optional.
The CSS rule that turned "Optional" red is fixed. The privacy page lists the new fields.
The Mobile number check was not working in current browsers, so I fixed it (see Deviations).

## Files changed
- `templates/product_enquiry.html`: fields put in the R10 order. `required` is now only on name, phone and category. Added the Area field and the visit-time `<fieldset>` (legend, Day/Time selects whose values are the readable text, a `data-visit-date` date wrapper, and the `#visit-time-note` hint). Email renamed `email_address` and made optional. Company label is now "Company name (if it's for a business)" and optional. Required marks use `.required-mark`. New Details placeholder. Service side-panel line changed to "When suits you: pick a day and time in the form". New submit-row sentence (R13). Mobile pattern brackets escaped.
- `static/js/enquiry.js`: new visit-time section: `isoLocal()`, `daysFromToday()`, `syncVisitDate()` (runs on load, on day `change` and on `pageshow`), date min = today and max = today + 30, a custom message for "Pick a date" with no date, and choosing a date switches Day to "Pick a date". Added `shortDate()` and `visitTimeText()`, and `orNotGiven()`. `emailPayload()` rebuilt in R15 order with an "Email address" row, and `_replyto` is only added when an email was given. Prefill, type, variant, card, reference, submit, error and storage code are unchanged.
- `templates/_contact.html`: email is `name="email_address"`, no longer required, and labelled "Optional". `.required-mark` on required labels. New submit-row sentence. Mobile pattern brackets escaped.
- `static/js/contact.js`: reads `email_address`. The row is renamed "Email address" and shows "Not given" when empty. `_replyto` is only sent when an email was given.
- `static/css/style.css`: `.form-field label > span:first-child` replaced by `.required-mark` (the bug fix). Added `.visit-time` (fieldset reset), `.visit-time legend` and `.form-hint`.
- `templates/privacy.html`: "What we collect" list changed to the R28 wording.
- `app.py`: `PRIVACY_UPDATED = "16 November 2026"`.

## Requirements covered
- R1–R4: `required` attributes in `product_enquiry.html`. Email has `type="email"` but no `required`. `_replyto` is only sent when there is an address (`emailPayload()`).
- R5: same characters and length (`[0-9+\(\)\- ]{7,24}`), and the browser now actually applies it (see Deviations). Since rework round 2 it must also contain at least 7 digits.
- R6: `#area` (maxlength 120, `autocomplete="address-level3"`).
- R7, R10 (AC10): Day/Time selects with the owner's choices. The date min/max are set in the browser with `isoLocal` (no UTC bug). Sundays are allowed.
- R8: `#visit-time-note`, tied to the fieldset with `aria-describedby`.
- R9: the fields are shown for every enquiry type (not tied to the variant).
- R10: DOM order = Name, Mobile, Category, Details, Area, Visit time, Email, Company, Comments (checked in the rendered HTML).
- R11: grey `.optional-label` on every optional field. The red colour now only applies to `.required-mark`.
- R12: new side-panel line and Details placeholder. Hero, card and call button are untouched.
- R13: "Your enquiry is emailed to our team. We'll call you back on your mobile (or reply by email if you give one). See our privacy policy." (both forms).
- R14–R16: `emailPayload()` rows, `visitTimeText()` and `orNotGiven()`.
- R17, R18, R20–R22: no change to subject, reference, routing, prefill, storage, honeypot or error code (checked in the harness below).
- R19: the no-JS form posts `area`, `visit_day`, `visit_time`, `visit_date` and `email_address`. The date box is visible without JS. Browser `required` checks apply.
- R23, R24: `_contact.html` and `contact.js`.
- R25: a `<fieldset>` and `<legend>` group the visit-time controls, and every control has its own `<label for>`.
- R26: browser `reportValidity()`. The mobile pattern now works, so "abc" is reported.
- R27: the new controls use the existing `.form-field` input/select styles (52px). Mobile keeps `type="tel" inputmode="tel"`.
- R28: privacy list and date.

## Deviations from design
1. **Mobile number pattern fixed (both forms).** The existing `pattern="[0-9+()\- ]{7,24}"` is rejected by Chromium/Edge. They now compile `pattern` in strict regex `v` mode, where a bare `(` `)` inside `[...]` is an error ("Invalid character in character class"), so the browser **ignored the pattern** and accepted any text, e.g. `abc`. That would fail AC3. It is now `[0-9+\(\)\- ]{7,24}`. This is the same rule, and it is also valid in older `u`-mode browsers. Tested in headless Edge: `abc` and `12` are rejected, while `+91 98765 43210`, `040-1234 5678` and `(040) 1234-5678` are accepted. This bug was already on the live site before this change.
2. In `shortDate()` the commas that `en-IN` puts in ("Tue, 17 Nov") are removed, so the row reads "Tomorrow (Tue 17 Nov), Morning (9am–12pm)" exactly as the design shows.
3. When Day is chosen but Time is "Any time", the time part is written in lower case ("Tomorrow (Tue 17 Nov), any time"), as the design's example shows.

## Checks run
- `.venv/Scripts/python tools/check_site.py`: **ALL CHECKS PASSED** (includes the static build and the internal link check). Run before and after the final edits.
- `node --check` on both scripts: OK.
- Rendered-HTML check (Flask test client): field order and `required` flags as in R10/R1. On `/`, only name, phone, topic and message are required. /privacy/ shows the new date and list.
- **Headless Edge harness, no real sends.** `window.fetch` was replaced by a stub that records the payload and then fails, and `formsubmit.co` was also mapped to a dead local port. Results:
  - Minimal (name, mobile, category Repair): Area, Visit time, Details, Email address and Company are all "Not given", Comments is "None", there is **no `_replyto` key**, and the subject is "New service enquiry: Repair (AR-261116-…)". The failure message "couldn't be sent … call us on +91 88013 81405" appears, the button works again, and session storage is not written.
  - Prefilled `/enquiry/?service=repair&category=Repair&product_description=…&comments=…`: the title reads "Enquire about Repair", the eyebrow "Service enquiry", and Details/Comments are prefilled. The full send gives `"Preferred visit time": "Tomorrow (Tue 17 Nov), Morning (9am–12pm)"`, Area is Kukatpally, `_replyto` is the given email, the rows are in R15 order, and Page is https://arcooling.in/services/repair/.
  - Pick a date with 2026-11-20 and Any time gives "Fri 20 Nov 2026, any time". Pick a date with no date is blocked with "Choose a date, or pick another day option." A past date is blocked ("must be 16-11-2026 or later"). Pick a date → date → back to Today clears the date, and the send works ("Today (Mon 16 Nov), Evening (4pm–7pm)").
  - The date box is hidden on load, with min 2026-11-16 and max 2026-12-16.
  - An empty form is blocked on name, phone and category. `name@` is blocked. `abc` in Mobile is blocked on both forms.
  - Contact form without email: "Email address": "Not given" and no `_replyto`. With an email: `_replyto` is set.
- Rework round 2: the Mobile hint (`title`) now ends "with at least 7 digits" so the browser message explains the new 7-digit rule.
- Screenshots at 375px, 320px (in iframes, because headless Edge will not go below a 504px viewport) and 1280px: no layout break. The visit-time selects stack on phones and sit side by side on desktop. "Optional" is grey.

## What the tester's real sends (T1–T4) should look like
All four go to `https://formsubmit.co/ajax/enquiry@arcooling.in` (T3 posts to the no-JS fallback inbox URL instead).
- **T1** (JS, /enquiry/, name + mobile + one category only). Subject `New <type> enquiry: <category> (AR-YYMMDD-NNNN)`. Table rows in this order: Reference, Enquiry type, Enquiring about, Name, Mobile, Area / locality = **Not given**, Preferred visit time = **Not given**, Category, Details = **Not given**, Comments = **None**, Email address = **Not given**, Company = **Not given**, Page = **Enquiry form**. No `_replyto` in the request payload. The thank-you page shows the name and reference.
- **T2** (JS, /services/repair/ → Book/Enquire, all fields). Subject `New service enquiry: Repair (AR-…)`. Area / locality = Kukatpally. Preferred visit time = `Tomorrow (<Day DD Mon>), Morning (9am–12pm)`. Details and Comments come from the prefill (or whatever was typed). Email address = the agreed email, Company = as typed, Page = `https://arcooling.in/services/repair/`. The payload contains `_replyto`, so Reply in the inbox should go to that email.
- **T3** (no JS, /enquiry/). Subject is the generic `New enquiry from AR Cooling Solutions website`. Raw field names appear in the table: name, phone, category, details, area, visit_day = `Pick a date`, visit_time (e.g. `Afternoon (12pm–4pm)`), visit_date = `YYYY-MM-DD`, **email_address (empty)**, company (empty), comments (empty), plus empty reference/enquiry_type/enquiring_about/page_link (these were empty on the no-JS path before too). There is no field called `email`, so Reply goes to FormSubmit's default. FormSubmit should redirect to /enquiry/thank-you/. Note: when sent from 127.0.0.1, `_next` points at the live site's thank-you page (`site_url`), so landing on https://arcooling.in/enquiry/thank-you/ is expected.
- **T4** (JS, home page contact form, no email). Subject `New enquiry from the contact section: <topic> (AR-…)`. Rows: Reference, Enquiry type = Quick enquiry, Looking for, Name, Email address = **Not given**, Mobile, Message, Page. No `_replyto`. The thank-you page shows the reference.

## Commits
- `03ceabd` Quicker enquiry form: only name, mobile and category required (code, docs 01–03 and the research backlog)
- `b44287b` Enquiry forms: reset the button after Back, block names/mobiles of only spaces (rework round 1, plus 04-test-report.md and updated 01)

## Rework log
### Round 1 (after 04-test-report.md and the owner decisions adding R29/R30, AC17/AC18)
The test report had no must-fix code defect (FAIL only because FormSubmit needs activation,
which the owner is handling). The owner asked for Defects 1 and 2 to be fixed; Defect 3 was
trivial, so it is fixed too. Nothing was sent to FormSubmit.

- **Defect 1 / R29 / AC17: button stuck on "Sending…" after Back.**
  `static/js/enquiry.js`: the primary button's label is now saved once when the page loads,
  and a `resetButtons()` helper re-enables all submit buttons and restores the label. It runs
  on a failed send (as before) and on `pageshow` when `event.persisted` is true (page restored
  from the back/forward cache). The existing visit-date `pageshow` re-sync is unchanged.
  `static/js/contact.js`: same, for the single button on the home page contact form.
- **Defect 2 / R30 / AC18: name or mobile of only spaces.**
  - No-JS path (and a backstop for JS): `templates/product_enquiry.html` and
    `templates/_contact.html`. Name gets `pattern=".*\S.*"` with title "Please enter your
    name". Mobile pattern is now `(?=.*[0-9])[0-9+\(\)\- ]{7,24}` (must contain at least one
    digit; same 7–24 length and characters as before, same v-mode-safe escaping).
    Checked in headless Edge (v-mode): "   " and "       " are blocked; "abc" still blocked;
    "+91 98765 43210" and "(040) 1234-5678" still accepted.
  - JS path: *(corrected in round 2)* this round added a `clearBlank()` step meant to empty
    a value of only spaces so the browser would say "Please fill in this field". It never
    ran: the browser checks `pattern` before the script's submit handler is called, so the
    visitor sees "Please match the requested format." plus the box's hint. That message is
    clear enough, so round 2 removed the dead code (see below).
- **Defect 3 (cosmetic): Company box 19px lower than Email at ~601px.**
  New `.form-field-bottom { align-content: end; }` in `static/css/style.css`, applied to the
  Email and Company fields in `templates/product_enquiry.html`, so both boxes sit on the same
  line when the Company label wraps. No effect on phones (one column) or wide screens.

Checks: `node --check` on both scripts; `.venv/Scripts/python tools/check_site.py` → ALL CHECKS PASSED.

**For the tester:** AC17 needs a real (or stubbed) successful send then Back, on /enquiry/
and on the home page form. AC18: "   " in Name is blocked on both forms, with and without JS,
by the pattern ("Please match the requested format." / "Please enter your name"; corrected
in round 2). Recheck the Email/Company row at 601px and that the stacked layout at ≤600px is
unchanged.

### Round 2 (after "Retest (round 1)" in 04-test-report.md and the owner decisions in 01)
Two small clean-ups the owner asked for. Nothing was sent to FormSubmit.

- **Defect 5: `clearBlank()` never ran.** Removed from `static/js/enquiry.js` and
  `static/js/contact.js` (the function and its call). The forms have no `novalidate`, so the
  browser's `required`/`pattern` check runs before the submit handler; spaces-only names and
  mobiles are blocked there, with and without JS, with "Please match the requested format."
  and the box's hint. The round-1 entry above is corrected. Nothing changes for the visitor.
- **Defect 6: "      1" was accepted as a mobile.** Both `templates/product_enquiry.html` and
  `templates/_contact.html` now use
  `pattern="(?=(?:[^0-9]*[0-9]){7})[0-9+\(\)\- ]{7,24}"`: the look-ahead needs at least 7
  digits anywhere in the value; the allowed characters, 7–24 length and v-mode-safe escaping
  are unchanged. It is a plain HTML check, so it works without JavaScript too. The hint
  (`title`) is now "Digits, spaces and + ( ) - only, with at least 7 digits", so the visitor
  knows why a short number is refused (small wording change, not in the design). The Jinja
  comment above each box says why the look-ahead is there.
  Checked in headless Edge 157 (v-mode), with the inputs copied from the pages the app
  renders for /enquiry/ and / : passes `+91 98765 43210`, `040-1234 5678`,
  `(040) 1234-5678`, `9876543210`, `1234567`; blocked (`Please match the requested format.`)
  `"      1"`, `abc`, `12`, `+-() ()-`, 7 spaces, `123456`, `123 456`. Name `"   "` and
  `" 	  "` still blocked; `"  Tester  "` still passes.

Checks: `node --check` on both scripts; `.venv/Scripts/python tools/check_site.py` → ALL CHECKS PASSED.
