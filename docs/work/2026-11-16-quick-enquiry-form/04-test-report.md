# Test report: Quicker enquiry form for home customers (backlog N1) — FAIL (blocked at Part B, no code defect)

**In short:** Part A (local checks, no real sends) **passed**: every check that can be done without a
real email works. Part B (real sends) **stopped after the first send**. FormSubmit answered T1 with
*"This form needs Activation. We've sent you an email containing an 'Activate Form' link."*, so the
stop rule applied. T2–T4 were **not sent**. That means AC1/AC4/AC5/AC9/AC11 are still unproven
on the delivery side (does the email arrive, what does Reply do, is an empty email accepted). The
requirements say these must be proven before merging. So the overall verdict is FAIL/blocked. I
found no must-fix code defect. **The owner needs to decide** how to get the real sends done (see
"Owner decision needed" at the end).

## Environment
- Branch `feature/quick-enquiry-form`, commit `4c1cfff` (code in `03ceabd`). Working tree was clean, and no code was edited.
- Server: `serve.py` (Waitress) on `http://127.0.0.1:8791`, with a throwaway database (`AR_DATABASE_PATH` set to a temp file) and a 40+ character test `SECRET_KEY`.
- Browser: headless Microsoft Edge 157, driven by DevTools Protocol from a small stdlib Python script (temp folder, not in the repo). Phone viewport 375×800 (mobile emulation) unless stated. Also tested at 320, 600, 601 and 1280.
- **No real sends in Part A**: `formsubmit.co` was mapped to a dead port (`--host-resolver-rules`) and also failed at the request stage by DevTools `Fetch`. The page's own `fetch` was wrapped only to *record* the JSON body (the real call still ran and failed). To test the success path, a test-only switch in session storage made the wrapper return `{"success":"true"}` without any network call. Google Tag Manager/Analytics were also blocked so tests didn't add visits to the owner's analytics.
- Clock checks: real clock (16 Nov 2026, IST), plus one run with a fixed clock of 02:00 IST and the time zone set to Asia/Kolkata.

## Regression
`.venv/Scripts/python tools/check_site.py` → **ALL CHECKS PASSED**. This covers every public page, the 404 page, the 9 share pages and their 404, the sitemap/robots/favicon, the admin lock, the login token, saving without a token being refused, and the static build: "Built 153 pages + 404 … All internal links and sitemap OK". The built `_site/enquiry/index.html` contains the new `visit_day`/`email_address`/`area` fields, and no `name="email"` remains in `_site/enquiry/` or `_site/index.html`.

## Acceptance criteria

| AC | Result | Evidence |
|---|---|---|
| AC1 | **Part A PASS / delivery NOT VERIFIED** | Minimal send (name, `+91 98765 43210`, Repair). Payload: `Area / locality`, `Preferred visit time`, `Details`, `Email address`, `Company` = "Not given", `Comments` = "None", `Page` = "Enquiry form", **no `_replyto` key**, subject `New service enquiry: Repair (AR-261116-2872)`. Success path (faked): lands on `/enquiry/thank-you/`, which shows "Thank you, Tester." and "Reference AR-261116-6765". The real send (T1) was refused by FormSubmit with an activation request (see Part B). |
| AC2 | PASS | `button.click()` on an empty or partly filled form. Name empty: focus moves to `name` with "Please fill out this field.", nothing sent. Mobile empty: focus on `phone`, same message. Category empty: focus on `category`, "Please select an item in the list." Nothing was sent in any case (`__sent` = 0, no status message). The browser bubble names the field via its label (accessible names checked: "Full name", "Mobile number", "Enquiry category"). |
| AC3 | PASS | `abc`, `12` and a 25-digit string are all blocked, with focus on phone and "Please match the requested format." (title hint "Digits, spaces and + ( ) - only"). `name@` is blocked with "Please enter a part following '@'. 'name@' is incomplete." `+91 98765 43210`, `040-1234 5678` and `(040) 1234-5678` are accepted. Same results on the home page contact form (`abc` and `name@` blocked). The pattern fix works: `[0-9+\(\)\- ]{7,24}`. |
| AC4 | **Part A PASS / delivery NOT VERIFIED** | From /services/repair/ (clicked the real Book link), filled with Kukatpally, Tomorrow, Morning, email, company. Payload rows in order: Reference, Enquiry type, Enquiring about, Name, Mobile, Area / locality = "Kukatpally", Preferred visit time = "Tomorrow (Tue 17 Nov), Morning (9am–12pm)", Category, Details, Comments, Email address, Company, Page. `_replyto` = the given email. This wording matches the coordinator's agreed format. Reply-in-inbox is not proven (T2 not sent). |
| AC5 | **NOT VERIFIED** | Needs a delivered T1 email. Code-side: no `_replyto` and no field named `email` when the email is empty (checked in the payload). |
| AC6 | PASS | At 375px the rendered order (top positions) is name 1067, phone 1162, category 1258, details 1354, area 1508, visit day 1631, time 1727, email 1864, company 1960, comments 2056. Only the first three are `required` and carry `.required-mark` (computed colour rgb(180,55,47) = `--danger` #b4372f). Every "Optional" tag, including the "Preferred visit time" legend, is rgb(138,131,137) = `--muted` #8a8389. The home page contact form has Email address "Optional" in muted grey, and name/phone/topic/message are required in red. |
| AC7 | PASS | `#visit-time-note`: "We're open Mon–Sat, 9am–7pm. We'll call you to confirm the time." It is tied to the fieldset by `aria-describedby`. The service panel now says "When suits you: pick a day and time in the form". The Details placeholder is "AC brand/model, capacity, quantity, or the problem you're seeing". Neither asks for area or time. |
| AC8 | **Part A PASS / delivery NOT VERIFIED** | Reached by clicking the page's own Enquire link each time. **Service** /services/repair/: card "Repair", h1 and title "Enquire about Repair", eyebrow "Service enquiry", category Repair, Details and Comments prefilled from the link, service panel shown, subject `New service enquiry: Repair (AR-…)`, Page `https://arcooling.in/services/repair/`. **Product** /products/split-ac-units/: card "Split AC units", eyebrow "Product enquiry", subject `New product enquiry: Split AC units (AR-261116-3474)`. **Spare part** /parts/compressors/copeland-zr28k3/: card "Copeland ZR28K3", eyebrow "Spare part enquiry", category Compressors, subject `New spare part enquiry: Copeland ZR28K3 (AR-261116-4231)`. All go to `https://formsubmit.co/ajax/enquiry@arcooling.in`. |
| AC9 | **Blocking part PASS / delivery NOT VERIFIED** | With scripts disabled (`Emulation.setScriptExecutionDisabled`), the form posts to `https://formsubmit.co/enquiry@arcooling.in` (non-ajax) as a normal form. An empty name is blocked (focus on name, no request). The date box is visible (80px tall) with no min/max, and it can be filled. The captured POST body (blocked before it left the PC) is `…&_next=https://arcooling.in/enquiry/thank-you/&…&name=…&phone=%2B91+88013+81405&category=Repair&details=…&area=Kukatpally&visit_day=Pick+a+date&visit_time=Afternoon+(12pm–4pm)&visit_date=2026-11-20&email_address=&company=&comments=`. There is no field called `email`. Whether FormSubmit accepts it and redirects (T3) is not proven. |
| AC10 | PASS | Date box hidden on load. min `2026-11-16` and max `2026-12-16` (today + 30). Pick a date with no date gives "Choose a date, or pick another day option." with focus on the date. 2026-11-15 gives "Value must be 16-11-2026 or later." 2026-12-17 gives "…16-12-2026 or earlier." 2026-12-16 is accepted ("Wed 16 Dec 2026, any time"). Sunday 2026-11-22 is accepted ("Sun 22 Nov 2026, Evening (4pm–7pm)"). Pick a date → date → Today clears the date, hides the box and sends "Today (Mon 16 Nov), Afternoon (12pm–4pm)". Pick a date → No preference sends "Not given". Typing a date while the day is "No preference" switches the day to Pick a date. At **02:00 IST** (UTC still 15 Nov), min = `2026-11-16` (correct; `toISOString` would have given 15 Nov) and Tomorrow = "Tue 17 Nov". **Back button:** after choosing Pick a date + 20 Nov and leaving for /privacy/, Back restores Day = Pick a date, the date visible and required, and the date kept. After a successful send, Back restores the same consistent state (no hidden required field). See Defect 1 for the submit button after Back. |
| AC11 | **Part A PASS / delivery NOT VERIFIED** | Home contact form, no email: payload `"Email address": "Not given"`, **no `_replyto`**, subject `New enquiry from the contact section: Service (AR-…)`. With `t@example.com`: `_replyto` = `t@example.com`. Success path (faked): thank-you page shows "Spare part enquiry received", "Thank you, Tester." and the reference, and storage is `{name, about, type, reference}`. T4 was not sent. |
| AC12 | PASS (local) | Session storage `ar-enquiry` after a send = `{"name":"Tester","about":"Repair","type":"service","reference":"AR-261116-3187"}` (only the 4 keys). It is not written on a failed send. During a send the only non-GET requests are `OPTIONS` + `POST https://formsubmit.co/ajax/enquiry@arcooling.in`, with none to 127.0.0.1 or arcooling.in. (Google Analytics loads on these pages, which was there before this change. It sends a page view, not form data. Analytics wording is backlog N2.) |
| AC13 | PASS (keyboard) / screen reader by accessibility tree only | Tab from Full name visits: name → phone → category → details → area → visit_day → visit_time → email_address → company → comments → (privacy link) → Submit. With Pick a date chosen, the date comes after Time of day. Keyboard-only run: typed name and phone, ArrowDown on category, typed area, ArrowDown ×3 to Pick a date, ArrowDown ×2 to Afternoon, typed `20112026` into the date, pressed Enter. The send went out and landed on the thank-you page. The accessibility tree shows a fieldset with role **group**, name "Preferred visit time Optional" and description = the note. Labels: "Day", "Time of day", "Date if you chose "Pick a date"", "Area / locality Optional", etc. Phone is `type=tel inputmode=tel`. **NVDA/TalkBack were not run** (no screen reader in this environment). |
| AC14 | PASS | /privacy/ lists "your name and mobile number;", "if you choose to give them: your email address, company name, area / locality and preferred visit time;", "the product, service or spare part …". It shows "Last updated 16 November 2026". Note for the deployer: if the merge happens after 16 Nov, update `PRIVACY_UPDATED`. |
| AC15 | PASS | Network set offline (`Network.emulateNetworkConditions offline`) and Submit pressed. The button shows "Sending…", then the `role="alert"` box says "Sorry, your enquiry couldn't be sent (Failed to fetch). Please try again, or call us on +91 88013 81405." The button is enabled again and its label is restored. Pressing it again sends again. The same happened with formsubmit.co blocked, on both forms. |
| AC16 | PASS | check_site.py passes, and so does the build inside it (above). Layout: no horizontal scroll on /enquiry/ (service variant, Pick a date open) or / at 320, 375, 600, 601 and 1280 (`scrollWidth` = viewport; only the intended marquee/ticker strips run past the edge, as before). Selects stack at ≤600px (Day and Time both at x=35 with full width) and sit side by side from 601px. Screenshots were checked at 320, 375 and 1280. |

## Part B — real sends (owner-approved 4, stop rule)
Sent from the branch on `http://127.0.0.1:8791` in headless Edge, so the payload is exactly what the page builds. The payloads were first checked in a dry run with FormSubmit blocked.

| # | Time (IST) | Reference | Result |
|---|---|---|---|
| T1 | 16 Nov 2026, 15:09:19–15:09:32 | AR-261116-3629 | `OPTIONS` → 200. `POST https://formsubmit.co/ajax/enquiry@arcooling.in` → **HTTP 200, body `{"success":"false","message":"This form needs Activation. We've sent you an email containing an 'Activate Form' link. Just click it and your form will be actived!"}`**. The page showed its "couldn't be sent" message and did not go to the thank-you page. **Stop rule applied.** |
| T2 | — | — | **Not sent** (stopped) |
| T3 | — | — | **Not sent** (stopped) |
| T4 | — | — | **Not sent** (stopped) |

T1 payload (as sent): Name "TEST – please ignore", Mobile "+91 88013 81405", Category Repair,
Comments "TEST – please ignore (T1: name, mobile and category only; automated website test)",
every other optional row "Not given", no `_replyto`.

**What is in the inbox now:** probably **no enquiry email**. Instead there is one **FormSubmit
"Activate Form" email** for enquiry@arcooling.in, sent around 15:09 IST because of a submission from
the local test address. Nobody clicked the activation link. FormSubmit seems to activate forms per
website address, so this does not appear to affect the live https://arcooling.in form. The live
form was not tested, and nothing on the live site was changed.

**What each email should look like once the sends are done** (for the owner to check):
- **T1**: subject `New service enquiry: Repair (AR-…)`. Rows: Reference, Enquiry type = Service, Enquiring about = Repair, Name = TEST – please ignore, Mobile = +91 88013 81405, Area / locality = Not given, Preferred visit time = Not given, Category = Repair, Details = Not given, Comments = TEST – please ignore …, Email address = Not given, Company = Not given, Page = Enquiry form. Pressing Reply must not give an empty or broken address.
- **T2**: subject `New service enquiry: Repair (AR-…)`. Area / locality = Kukatpally, Preferred visit time = `Tomorrow (<day date>), Morning (9am–12pm)`, Details start "TEST – please ignore (T2 …)" followed by the Repair prefill, Comments "TEST – please ignore – Please contact me to schedule a visit.", Email address = enquiry@arcooling.in, Company = AR Cooling Solutions (TEST), Page = https://arcooling.in/services/repair/. Reply should go to enquiry@arcooling.in.
- **T3** (no JavaScript): subject `New enquiry from AR Cooling Solutions website`, raw field names: name, phone, category = Repair, details "TEST – please ignore (T3 …)", area = Kukatpally, visit_day = Pick a date, visit_time = Afternoon (12pm–4pm), visit_date = 2026-11-20 (use a date in the next 30 days on the day of sending), and empty email_address/company/comments/reference fields. The browser should land on /enquiry/thank-you/.
- **T4**: subject `New enquiry from the contact section: Service (AR-…)`. Rows: Reference, Enquiry type = Quick enquiry, Looking for = Service, Name, Email address = Not given, Mobile, Message "TEST – please ignore (T4 …)", Page. The thank-you page shows the reference.

## Edge cases
- Unknown URL `/enquiry/nope/` → 404. `/enquiry`, `/enquiry/thank-you` and `/privacy` → 308 to the trailing-slash URL. `/admin` and `/admin/` (logged out) → 302 to `/admin/login`. Saving or logging in without a CSRF token is refused (check_site).
- HTML/script in link parameters (`?service=<script>…`, `comments=<img onerror>`, `product_description="><svg onload>`): shown as plain text in the fields, no element is injected, and the alert hook never fired. An unknown `?product=`/`?part=` gives the plain "Enquiry" page with no card.
- Long text: Area is capped at 120 characters and Details at 1000 (typed input). Unicode and special characters in the name (`Zoë O'Brien & <Sons> "quoted" తెలుగు`) arrive in the payload unchanged. An email with spaces around it is trimmed, and the same trimmed value is used for `_replyto`.
- A past date without JavaScript is accepted, because there is no min/max without JS. The design accepts this.
- A name of only spaces passes the browser's `required` check and is sent as an empty Name (Defect 2).

## Defects
1. **should-fix (was already there before this change, not caused by it):** after a successful send, pressing the browser's **Back** button returns to a form whose Submit button is still disabled and reads "Sending…", on both /enquiry/ and the home page contact form. The browser restores the page from its back/forward cache (`pageshow.persisted = true`), and nothing re-enables the button. The same code is on `main`.
   *Steps:* send an enquiry (success) → thank-you page → Back. *Expected:* a usable form. *Actual:* the button is disabled, labelled "Sending…", and the visitor must reload the page. (The visit-date part of Back works correctly.)
2. **minor (was already there):** a Full name of only spaces (and a mobile of 7 spaces) passes the browser checks. The enquiry then sends with an empty Name row.
   *Steps:* name "   ", mobile 9876543210, category Repair → Submit. *Expected:* blocked. *Actual:* sent with `"Name": ""`.
3. **minor (cosmetic):** between about 601px and a mid-size width, the long label "Company name (if it's for a business) Optional" wraps to two lines. The Company box then sits about 19px lower than the Email box beside it (at 601px: email top 1799, company 1818). It lines up at 1280px.
4. **blocker for sign-off (not a code defect):** FormSubmit requires activation for sends from the local test address, so the real-send checks (AC1, AC4, AC5, AC8 delivery, AC9, AC11) could not be completed.

## Owner decision needed
Choose one:
- **(a)** Do **not** activate the local form. After merging, do the same 4 labelled sends on https://arcooling.in, as 02-design suggests. The live form address is presumably already activated, so it should accept them. If any one fails, the owner can revert. *Or*
- **(b)** Click the "Activate Form" link in the FormSubmit email for the local test address, then let the tester send T1 (again), T2, T3 and T4 from the branch. That is 4 more sends, which needs a fresh OK because the approved 4 included the T1 attempt that was refused.

Until then, AC1/AC4/AC5/AC9/AC11 delivery and Reply behaviour stay unverified.
