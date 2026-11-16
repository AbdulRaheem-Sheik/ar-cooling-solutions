# Quicker enquiry form for home customers (backlog N1)

## Goal
"Make the enquiry form quick for home customers." A person on a phone with a broken AC
should be able to send an enquiry with just their name, mobile number and what they need,
and can add their area and a preferred visit time without typing it into the message box.
**How the owner will know it worked:** more enquiry emails a week from the website
(compare the 4 weeks before and after going live), more of them from homeowners without
a company or email, and fewer call-backs where the team has to ask "which area are you in?"

## Users & context
- **Home customers in Hyderabad**, mostly on phones, often with an AC that has just stopped
  cooling. Many have no company name and may not want to type (or don't have to hand) an
  email address. They arrive on /enquiry/ from "Enquire" / "Book" buttons on service, product
  and spare-part pages (form already filled in for them) or from the menu (empty form).
- **Business customers** (offices, shops, factories): still want to give a company name and
  email; these fields stay, just not compulsory.
- **The AR Cooling team** reads the enquiry email (often on a phone) and calls back. They need
  the mobile number, area and preferred time at a glance, plus the reference number.

## Current behaviour
Live page: https://arcooling.in/enquiry/ (template `templates/product_enquiry.html`, script
`static/js/enquiry.js`, route `product_enquiry` in `app.py`).

**Fields today (in this order)**

| Field | Required? | Why it is required today |
|---|---|---|
| Full name | Yes | Needed to address the customer. |
| Company name | **Yes** | No technical reason. FormSubmit does not need it; the form was written with business buyers in mind. |
| Email address | **Yes** | Used as the email's "Reply-To" (`_replyto` in `emailPayload()`), so the team can press Reply. FormSubmit itself does not need the visitor's email to deliver the enquiry (FormSubmit's docs only say the value is used for Reply-To). |
| Mobile number | Yes | The team calls back. Accepts digits, spaces and `+ ( ) -`, 7–24 characters. |
| Enquiry category | Yes | Decides the enquiry type (product / service / spare / general), which picks the inbox (`ENQUIRY_INBOXES` in `app.py`, all currently `enquiry@arcooling.in`), the email subject and the page wording. |
| Product / service details | Yes | Free text. On prefilled links it is already filled in. |
| Comments | Optional | Free text. |

On a phone the fields are in one column, in the order above, so a visitor must get past
Company and Email before reaching Mobile.

**What the business relies on (must keep)**
- **Reference number** `AR-YYMMDD-NNNN`, made in the browser at send time, shown in the
  email and on the thank-you page (`/enquiry/thank-you/`, `templates/enquiry_thanks.html`,
  which reads name, "about", type and reference from the browser's session storage).
- **Enquiry type routing**: type comes from the prefilled item (`?product=`, `?service=`,
  `?part=`) or else from the chosen category; `data.endpoints[type]` picks the FormSubmit
  inbox (`get_enquiry_endpoints()` / `formsubmit_endpoint()` in `app.py`).
- **Email subject**: `New <type> enquiry: <what it's about> (<reference>)`, e.g.
  "New service enquiry: Repair (AR-261116-4821)".
- **Email layout**: FormSubmit "table" template with rows in a fixed order: Reference,
  Enquiry type, Enquiring about, Name, Company, Email, Mobile, Category, Details, Comments
  ("None" if empty), Page.
- **Prefilled links**: `product_enquiry_url`, `service_enquiry_url`, `spare_enquiry_url` in
  `app.py` add `?product=` / `?service=` / `?part=` (drives the "You're enquiring about"
  card, the heading "Enquire about …" and the page title) plus `?category=`,
  `?product_description=` (→ Details) and `?comments=` (→ Comments). Example:
  `/enquiry/?service=repair&category=Repair&product_description=...&comments=Please contact me to schedule a visit.`
- **Service wording**: for service enquiries the page swaps to "Book a service visit" text,
  whose side panel asks for "Your area and preferred visit time", but there is no field for
  either, so customers must type them into Details.
- **Spam trap** (`_honey`) and `_captcha=false`.

**No-JavaScript fallback**: the form posts straight to FormSubmit's general inbox
(`fallback_action`), and FormSubmit sends the visitor to the thank-you page (`_next`).
In this case there is no prefill, no reference number, the subject is the generic
"New enquiry from AR Cooling Solutions website", and FormSubmit receives the raw field
names (name, company, email, phone, category, details, comments).

**Quick enquiry form in the contact section** (`templates/_contact.html`,
`static/js/contact.js`; on the home page and other pages that include the contact
section): Full name, Mobile, **Email (required)**, Looking for (select), Message, all
required. Same FormSubmit flow, same reference number format, subject
"New enquiry from the contact section: <topic> (<reference>)", `_replyto` = email.

**Privacy page** (`templates/privacy.html`, "What we collect"): lists "your name and
company name; your email address and mobile number; the product, service or spare part …
and any details or comments". It does not mention area or preferred time, and reads as if
company and email are always collected. `PRIVACY_UPDATED` in `app.py` holds the
"last updated" date (currently 20 October 2026).

**Small styling issue seen in code**: the CSS rule that colours the required `*` red
(`.form-field label > span:first-child` in `static/css/style.css`) also matches the grey
"Optional" tag on Comments, so "Optional" very likely shows in the same red as required
marks. Worth checking on screen, because this change adds several optional fields.

## Requirements

### Required vs optional
- **R1.** On /enquiry/ only these are required: **Full name**, **Mobile number** and
  **Enquiry category** ("what you need"). Everything else is optional.
- **R2.** **Product / service details** becomes optional (see Open question Q2). Prefilled
  links still fill it in as today.
- **R3.** **Company name** becomes optional. Its label makes clear it is only for
  businesses, e.g. "Company name (if it's for a business)".
- **R4.** **Email address** becomes optional. When it is given it must still be a valid
  email address, and it is still used as the email's Reply-To. When it is left empty the
  enquiry still sends successfully and nothing broken or blank is used as Reply-To.
- **R5.** Mobile number keeps today's rules (digits, spaces, `+ ( ) -`, 7–24 characters)
  so numbers like `98xxxxxxxx`, `+91 98xxx xxxxx` and `040-xxxx xxxx` all work.

### New optional fields
- **R6.** Add an optional **"Area / locality"** text field (e.g. "Kukatpally", "Banjara Hills"),
  max length similar to other short fields.
- **R7.** Add an optional **"Preferred visit time"**, made of two simple choices: a **day**
  and a **time of day** (the exact choices are Open question Q1; build with the proposed
  default). Both default to "No preference / any time", so a visitor can skip them.
  If a "Pick a date" style choice is offered, dates in the past cannot be chosen.
- **R8.** Next to the preferred time, the page says in plain words that this is a request,
  not a confirmed booking, e.g. "We'll call you to confirm the time."
- **R9.** Area and preferred visit time are shown for every enquiry type (service, product,
  spare part, general), because deliveries and site surveys need them too (see Q3).

### Layout and wording (mobile first)
- **R10.** On a phone the fields appear in this order: Full name, Mobile number, Enquiry
  category, Details, Area / locality, Preferred visit time, then the optional Email,
  Company name and Comments. So all required fields come first and a visitor can stop
  after the first three and press Submit.
- **R11.** Each optional field shows the word "Optional" (text, not colour alone), styled
  so it does not look like the red required mark. Required fields keep the `*` and the
  "* Required" note.
- **R12.** Page text no longer asks people to type their area or preferred time in the
  message box: the service side panel and the Details placeholder are updated to match the
  new fields. Other wording (hero, "You're enquiring about" card, call button) stays.
- **R13.** The line under the form keeps saying how we reply, adjusted so it does not
  promise email when none was given, e.g. "We'll call you back on your mobile (or reply by
  email if you give one)." with the privacy policy link.

### Email the team receives
- **R14.** The emailed table includes new rows **Area / locality** and **Preferred visit
  time** (day and time of day together in one readable row, e.g. "Tomorrow, Morning
  (9am–12pm)").
- **R15.** Row order puts call-back details near the top: Reference, Enquiry type,
  Enquiring about, Name, Mobile, Area / locality, Preferred visit time, Category, Details,
  Comments, Email, Company, Page.
- **R16.** Any optional field left empty shows "Not given" (Comments may keep "None"), never
  a blank or missing row, so the table always has the same rows.
- **R17.** Subject line format, reference number format, enquiry type labels and inbox
  routing are unchanged.

### Things that must keep working
- **R18.** Prefilled links from product, service and spare-part pages (`?product=`,
  `?service=`, `?part=` with `?category=`, `?product_description=`, `?comments=`) still
  show the "You're enquiring about" card, heading, page title, chosen category, Details and
  Comments exactly as today, and route to the right enquiry type.
- **R19.** Without JavaScript, the form still posts to FormSubmit and lands on the
  thank-you page; the new fields are included in that email, and the required/optional
  rules of R1–R4 apply (the browser's own checks). Any "pick a date" choice must be usable
  without JavaScript.
- **R20.** The thank-you page still shows the visitor's name, what it's about, the enquiry
  type and the reference number after a JavaScript send.
- **R21.** Nothing about the visitor is stored on the server: the enquiry still goes from
  the browser to FormSubmit only. Session storage on the visitor's browser stays limited to
  name, about, type and reference (no area, time, mobile or email added).
- **R22.** The spam trap and the "couldn't be sent … please call us on …" error message
  still work.

### Quick enquiry form in the contact section
- **R23.** In the contact-section quick enquiry form, **Email** becomes optional with the
  same behaviour as R4 (valid if given; send works without it; no blank Reply-To). Its label
  shows "Optional" (R11). No other fields are added or removed there; it stays short.
- **R24.** Its email table shows "Not given" for an empty email (R16) and its subject,
  reference and thank-you flow are unchanged.

### Accessibility
- **R25.** Every new field has a visible label tied to the field; the day and time-of-day
  choices are grouped under the visible "Preferred visit time" heading so screen readers
  announce them together.
- **R26.** If a required field is empty or the mobile/email format is wrong, the visitor
  gets a message that names the field and what to fix, focus moves to that field, and the
  message is announced to screen readers (today's browser checks are acceptable if they do
  this).
- **R27.** New fields work with keyboard only and are at least as large to tap as the
  existing fields; the mobile field still opens the phone's number keypad.

### Privacy page
- **R28.** "What we collect" on /privacy/ lists: name and mobile number; **optionally**
  email address, company name, area / locality and preferred visit time; and what the
  enquiry is about with any details or comments. The "last updated" date changes to the
  release date.

## Acceptance criteria
Test on a phone-sized screen (about 375 px wide) unless stated. Every real send goes to
the live enquiry inbox: mark test enquiries with the name "TEST – please ignore" and tell
the owner before sending.

- **AC1.** On /enquiry/ (no link parameters), fill only Full name, Mobile number and
  Enquiry category, press Submit: the thank-you page shows the name and a reference
  `AR-YYMMDD-NNNN`; the email arrives with that reference, Email/Company/Area/Preferred
  visit time/Details showing "Not given", and no error.
- **AC2.** Submit with Full name empty, then Mobile empty, then Category not chosen: each
  time the form does not send, a message names the missing field and focus moves to it.
- **AC3.** Type `abc` in Mobile, or `name@` in Email: the form does not send and explains
  the problem. `+91 98765 43210` in Mobile is accepted.
- **AC4.** Fill everything including Area "Kukatpally", day "Tomorrow", time "Morning",
  email and company: the email shows Area / locality = Kukatpally and Preferred visit time =
  "Tomorrow, Morning (9am–12pm)" (or the agreed wording), rows in the R15 order, and
  pressing Reply in the inbox addresses the visitor's email.
- **AC5.** For AC1's email (no visitor email), the email was delivered normally and
  pressing Reply does not produce an empty or broken address (it falls back to FormSubmit's
  normal sender behaviour).
- **AC6.** On a phone, the field order is exactly as R10; the first three fields are
  required and all others show "Optional" in text, not in the red required colour.
- **AC7.** The page text near the time choice says the time will be confirmed by phone;
  the service side panel and Details placeholder no longer ask the visitor to type area or
  preferred time.
- **AC8.** From /services/repair/ use an "Enquire"/"Book" button: the card "You're
  enquiring about Repair", the heading, title, category "Repair", Details and Comments are
  prefilled as before; the eyebrow reads "Service enquiry"; the email subject is
  "New service enquiry: Repair (AR-…)". Repeat from one product page (subject "New product
  enquiry: …") and one spare part (subject "New spare part enquiry: …").
- **AC9.** With JavaScript turned off, open /enquiry/, fill name, mobile, category, area and
  a preferred time, submit: FormSubmit accepts it, the browser lands on
  /enquiry/thank-you/, and the email includes area and preferred time. Leaving name empty
  is blocked by the browser. Any date choice can be used without JavaScript. Also send one
  no-JavaScript enquiry with email left empty and confirm FormSubmit accepts it.
- **AC10.** If a "pick a date" choice exists, a date before today cannot be selected.
- **AC11.** Contact-section quick enquiry (home page): send with name, mobile, topic and
  message but no email: it sends, the thank-you page shows the reference, and the email
  shows Email = "Not given". Sending with a valid email still sets Reply-To.
- **AC12.** In the browser's developer tools after a send, session storage `ar-enquiry`
  contains only name, about, type and reference. The only network request carrying the
  form goes to formsubmit.co (none to arcooling.in).
- **AC13.** Keyboard only: Tab through every field on /enquiry/ in the R10 order, choose a
  preferred day/time and submit without a mouse. A screen reader (e.g. TalkBack or NVDA)
  reads each new field's label and "Preferred visit time" for the time choices.
- **AC14.** /privacy/ "What we collect" lists the fields as in R28 and shows the new
  "last updated" date.
- **AC15.** Simulate a failed send (e.g. go offline before pressing Submit): the "couldn't
  be sent … call us on …" message appears and the button works again.
- **AC16.** `tools/check_site.py` and `tools/build_static.py` pass; /enquiry/ and the home
  page show no layout break at 320 px, 375 px and desktop widths.

## Out of scope
- New fields in the contact-section quick form (only email becomes optional there).
- Making visits bookable/confirmed online, calendars, or availability checks.
- Storing enquiries on the server, admin views of enquiries, SMS/WhatsApp notifications.
- Prefilling area or visit time from links; changing the subject line to include area.
- Adding a reference number to the no-JavaScript path (it has none today).
- Analytics or counting form sends, and the privacy page's "no analytics" wording (backlog N2).
- Splitting enquiry types to different inboxes (all still go to enquiry@arcooling.in).

## Risks
- **Empty email with FormSubmit:** FormSubmit's docs don't say what an empty Reply-To does.
  Sending an empty `_replyto` (or an empty field named `email` on the no-JS path) could be
  rejected or produce a broken Reply-To. Must be proven with real test sends (AC1, AC5,
  AC9, AC11) on both the JavaScript and no-JavaScript paths before merging.
- **Live inbox:** every test send lands in the real enquiry inbox the team works from;
  agree with the owner and label tests clearly.
- **Fewer email addresses collected:** the team will more often only have a phone number,
  so replies by email won't be possible for those enquiries. This is the intended trade-off.
- **Owner's email filters:** if the owner filters emails by subject, the subject is
  unchanged (R17); new rows only change the email body.
- **Category names come from the database** (admin can rename products/services); the
  required category list and routing must keep using the live categories, not a fixed list.
- **No URL changes:** /enquiry/ and /enquiry/thank-you/ keep their URLs; no SEO risk.
- **1 GB server:** no server work is added; everything stays in the page and FormSubmit.
- **Static GitHub Pages build** must still pass.

## Open questions
- **Q1. Preferred visit time choices.** Proposed default (fits Mon–Sat 9am–7pm):
  - Day: *No preference* (default) / *Today* / *Tomorrow* / *Pick a date* (date picker, today
    onwards, up to 30 days ahead).
  - Time of day: *Any time* (default) / *Morning (9am–12pm)* / *Afternoon (12pm–4pm)* /
    *Evening (4pm–7pm)*.
  - Note under it: "We're open Mon–Sat, 9am–7pm. We'll call you to confirm the time."
  Please confirm: (a) can we offer **"Today"** (same-day visits)? Default: yes, with the
  "we'll call to confirm" note. (b) Are these time bands right? (c) Should **Sunday** be
  selectable? Default: allowed, the note says we're closed Sundays and will confirm.
- **Q2. Is "Details" required?** Default: **optional**, because the category already says
  what they need (e.g. "Repair") and the team calls back anyway; prefilled links still fill
  it. Alternative: keep Details required.
- **Q3. Show area and visit time for every enquiry, or only for service enquiries?**
  Default: **every enquiry** (useful for deliveries and site surveys, and keeps the
  no-JavaScript form identical).

## Owner decisions (2026-11-16)
- Requirements **approved** as written (Details becomes optional = Q2 default).
- **Q1 visit time = as proposed**: Day: No preference (default) / Today / Tomorrow / Pick a date
  (today up to 30 days ahead, Sundays selectable); Time: Any time (default) / Morning (9am–12pm) /
  Afternoon (12pm–4pm) / Evening (4pm–7pm); note: "We're open Mon–Sat, 9am–7pm. We'll call you
  to confirm the time."
- **Q3 = default**: area and visit time shown for all enquiry types.
- **Real test sends approved**: the team may send about 3–4 test enquiries through FormSubmit to
  the live enquiry inbox, each clearly labelled "TEST – please ignore" (name and details), to
  check delivery with and without JavaScript and with email left empty. No other real sends.

## Owner decisions after testing (2026-11-16)
- **FormSubmit activation**: the T1 test from 127.0.0.1 was refused ("This form needs
  Activation"). The owner chose to **activate the local test form** (they click FormSubmit's
  Activate link), then the tester sends the **4 labelled test enquiries T1–T4 from the branch**
  before merge (4 new sends approved; the refused T1 attempt doesn't count).
- **Scope added**: fix two existing form bugs found by the tester, on /enquiry/ and the home
  contact form:
  - **R29** After a successful send, going Back must not leave the submit button stuck on
    "Sending…"/disabled (pages restored from the browser cache must reset the button).
  - **R30** Name (and Mobile) made only of spaces must be rejected like an empty field.
  - **AC17** Send (stubbed), press Back: the button reads its normal label and is enabled.
  - **AC18** A name of only spaces, or a mobile of only spaces, is blocked with the usual message.
