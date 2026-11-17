# Deployment: Quicker enquiry form for home customers (backlog N1)

## Prepare (2026-11-16)

- **Branch:** `feature/quick-enquiry-form` (based on current `main`, no other PR dependency)
- **Verdicts:** 04-test-report.md = PASS (retest round 2; delivery parts of AC4, AC8, AC9, AC11
  deferred to post-merge real sends by owner decision). 05-review.md = APPROVE (4 nits, no action needed).
- **PR link:** see `pr7url.txt` in the deployer's scratchpad and the deployer's reply (compare
  `main...feature/quick-enquiry-form`, quick_pull).
- **Server steps:** none beyond the usual auto-pull. Front-end only: no routes, packages,
  database, `data/` or `setup.sh` changes.

### Before merging
- `PRIVACY_UPDATED = "16 November 2026"` (`app.py:879`). If the merge happens on a later day,
  update it on this branch first so the privacy page date matches the merge date.

### After merging (owner-approved, not done yet)
Three real sends from https://arcooling.in, each labelled "TEST – please ignore", made by the
deployer while the owner watches the inbox (stop rule from 02/04 applies):
- **T2** (JS, Repair page, all fields): Reply goes to the given email (AC4); service subject right (AC8).
- **T3** (no JS, email empty): FormSubmit accepts it, browser lands on /enquiry/thank-you/, email
  shows area, visit_day, visit_date, visit_time (AC9). **A rejection here is grounds to revert.**
- **T4** (home page contact form, no email): AC11.
- Record times and references so the owner can delete the test emails.

### Follow-ups (non-blocking reviewer nits)
1. `docs/work/2026-11-16-hvac-website-research/01-requirements.md` was committed with this feature
   (harmless docs; would normally be its own commit/PR).
2. `static/js/enquiry.js:103-104`: date min/max set once on load; a page left open past midnight
   keeps yesterday selectable until reload.
3. `static/js/enquiry.js:108`: `syncVisitDate` runs again on the first `pageshow` (harmless no-op).
4. `templates/product_enquiry.html:144`: `.optional-label` reused just for grey styling on the
   date hint; don't read that class as "field is optional".
- Separate: privacy page says "no analytics" but Google Tag Manager/Analytics loads (backlog N2).
- A real screen reader (NVDA/TalkBack) was not run; owner may try TalkBack on a phone.

## Verify (2026-11-17)

**Result: LIVE AND WORKING.** All three approved test sends were accepted by FormSubmit; no revert needed.

- **Merge:** PR #7 merged as `de55f55` (16 Nov 2026, 19:28 IST). `origin/main` = `de55f55`; the PR head
  `32cac20` is in `main`. The branch's later commit `babb262` (privacy date → 17 Nov) is not merged and
  not needed (the merge was on 16 Nov).
- **Server:** `/opt/ar-cooling` is on `de55f55`. `ar-cooling` has been active since 16 Nov 14:03:34 UTC
  (19:33 IST), started by the auto-update on that commit, 0 restarts since. `ar-cooling-update` was run
  again on 17 Nov ~09:39 IST: nothing new to pull. Memory: 658 MB available, 9 MB swap used, load 0.1.
- **Journal (`journalctl -u ar-cooling`):** no errors or tracebacks. Only `WARNING:waitress.queue:Task
  queue depth is N` (max 8) during short bursts of requests (mostly 17 Nov 00:45 UTC, 225 lines in ~2 s;
  smaller bursts at 14:29, 15:09, 18:37, 20:11 UTC). Requests queued briefly and were served; see follow-ups.
- **Extra deployment steps:** none (front-end only).

### Live checks
| Check | Result |
|---|---|
| `tools/check_site.py --live` | **ALL CHECKS PASSED** (153 pages, admin, static build, 19 live pages, all 152 live sitemap pages, www redirect) |
| Live `static/js/enquiry.js` and `contact.js` | identical to `main` (ignoring line endings) |
| /enquiry/ fields | name (required, `pattern=".*\S.*"`), phone (required, `pattern="(?=(?:[^0-9]*[0-9]){7})[0-9+\(\)\- ]{7,24}"`, inputmode tel), category (required), details/area/visit time/email/company/comments optional; in the R10 order |
| /enquiry/ visit time | Day: No preference / Today / Tomorrow / Pick a date (+ date box usable without JS); Time: Any time / Morning (9am–12pm) / Afternoon (12pm–4pm) / Evening (4pm–7pm); note "We're open Mon–Sat, 9am–7pm. We'll call you to confirm the time." |
| /enquiry/ labels | "Optional" tag on Details, Area / locality, Preferred visit time, Email address, "Company name (if it's for a business)" |
| Home contact form | Email (`email_address`) optional with "Optional" tag; same new name/mobile patterns |
| /services/repair/ | Book/Enquire links go to `/enquiry/?service=repair&category=Repair&product_description=…&comments=Please contact me to schedule a visit.` (unchanged) |
| /privacy/ | "Last updated 16 November 2026"; "What we collect" lists name and mobile; "if you choose to give them: your email address, company name, area / locality and preferred visit time"; the product/service/part and details/comments (R28) |
| /enquiry/thank-you/ | 200 |

### Real test sends (owner-approved, once each, from the live origin)
Sent with a script that reproduces exactly what the live pages send (same JSON body / form fields,
`Origin: https://arcooling.in`, `Referer: https://arcooling.in/`, 30 s timeout, network errors logged,
stop rule armed). Mobile on all three: +91 88013 81405. Name on all three: "TEST – please ignore".

| Test | Time (IST, 17 Nov) | Reference | HTTP result |
|---|---|---|---|
| **T2** JS, from the Repair page link, all fields | 09:43:13–09:43:14 | **AR-261117-5016** | `OPTIONS` 200, `POST https://formsubmit.co/ajax/enquiry@arcooling.in` **200 `{"success":"true","message":"The form was submitted successfully."}`** (0.7 s) |
| **T3** no-JS, plain form POST, email empty | 09:43:26–09:43:27 | none (the no-JS path has no reference) | `POST https://formsubmit.co/enquiry@arcooling.in` **302 → `https://arcooling.in/enquiry/thank-you/`** (1.7 s); thank-you page answered 200. **Accepted.** |
| **T4** JS, home page contact form, no email | 09:43:39–09:43:40 | **AR-261117-2234** | `OPTIONS` 200, `POST https://formsubmit.co/ajax/enquiry@arcooling.in` **200 `{"success":"true",…}`** (0.6 s) |

No network errors, timeouts or activation requests. No retries were needed or made.

### What the owner should see in the enquiry@arcooling.in inbox (about 09:43 IST, 17 Nov)
Please confirm all three arrived, then delete them.

1. **T2** – subject **`New service enquiry: Repair (AR-261117-5016)`**. Table rows in this order:
   Reference = AR-261117-5016 · Enquiry type = Service · Enquiring about = Repair ·
   Name = TEST – please ignore · Mobile = +91 88013 81405 · **Area / locality = Kukatpally** ·
   **Preferred visit time = Tomorrow (Wed 18 Nov), Morning (9am–12pm)** · Category = Repair ·
   Details = "TEST – please ignore (T2: all fields, from the Repair page)" then "Repair service / AC brand / type: / Number of units: 1" ·
   Comments = TEST – please ignore – Please contact me to schedule a visit. ·
   Email address = enquiry@arcooling.in · Company = AR Cooling Solutions (TEST) · Page = https://arcooling.in/services/repair/.
   **Press Reply: it should address enquiry@arcooling.in** (AC4 Reply-To). (AC4, AC8)
2. **T3** – subject **`New enquiry from AR Cooling Solutions website`** (generic, no reference). Raw field
   names: name = TEST – please ignore · phone = +91 88013 81405 · category = Repair ·
   details = TEST – please ignore (T3: no JavaScript, email left empty) · **area = Kukatpally** ·
   **visit_day = Pick a date** · **visit_time = Afternoon (12pm–4pm)** · **visit_date = 2026-11-20** ·
   email_address, company, comments, reference, enquiry_type, enquiring_about, page_link empty (FormSubmit
   may hide empty rows). Reply goes to FormSubmit's normal sender address (no visitor email). (AC9)
3. **T4** – subject **`New enquiry from the contact section: Service (AR-261117-2234)`**. Rows:
   Reference = AR-261117-2234 · Enquiry type = Quick enquiry · Looking for = Service ·
   Name = TEST – please ignore · **Email address = Not given** · Mobile = +91 88013 81405 ·
   Message = TEST – please ignore (T4: home page contact form, no email) · Page = https://arcooling.in/.
   Reply goes to FormSubmit's normal sender address. (AC11)

If any of the three is missing after ~15 minutes (check spam too), tell the team: FormSubmit said it
accepted them, so a missing email would be a FormSubmit delivery problem, not the website.

### Follow-ups
- Owner: confirm the three emails above arrived and that Reply on T2 addresses enquiry@arcooling.in;
  then delete them.
- Branch `feature/quick-enquiry-form` still has unmerged `babb262` (privacy date → 17 Nov); not needed.
  The owner may delete the branch on GitHub when ready (the team does not delete branches).
- Waitress "Task queue depth" warnings: short request bursts (likely crawlers) briefly exceed the worker
  threads. No errors and the site stayed up; worth a look only if it grows (e.g. more threads in
  `serve.py`, or rate-limiting in Caddy).
- Reviewer nits and backlog N2 (analytics wording) from the prepare section still stand.

## Owner confirmation (2026-11-17)
All three test enquiries (T2 AR-261117-5016, T3 no-JS, T4 AR-261117-2234) arrived in the enquiry inbox. Delivery checks AC4, AC8, AC9 and AC11 are confirmed; the task is complete.
