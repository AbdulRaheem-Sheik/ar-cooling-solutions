# Review: Quicker enquiry form for home customers (backlog N1) — APPROVE

## Summary
Reviewed `git diff main...feature/quick-enquiry-form` (commits `03ceabd`, `4c1cfff`, `b44287b`,
`4672fd9`, `65ff94b`, `22189b8`, `ebabe96`) against 01 (including all three owner-decision
sections), 02 (including the coordinator decisions), 03 (rework rounds 1–2 and deviations) and
04 (PASS at round 2).

This change only touches the front end: two templates, two scripts, CSS, the privacy page text and
`PRIVACY_UPDATED`. There are no new routes, packages or database changes, and nothing extra runs
on the 1 GB server. The code is small and follows existing patterns, and the comments explain why.
I ran `.venv/Scripts/python tools/check_site.py` myself on the branch and got **ALL CHECKS PASSED**
(static build: 153 pages + 404, links and sitemap OK). The working tree was unchanged afterwards
apart from the expected uncommitted 04.

I found no must-fix or should-fix problems. The items I was asked to check:
- **FormSubmit payload safety:** neither form has a field named `email` any more. The inputs are
  `name="email_address"` in `templates/product_enquiry.html:156` and `templates/_contact.html:79`.
  The JS table row is labelled "Email address". `_replyto` is only added when an address was typed
  (`static/js/enquiry.js:208`, `static/js/contact.js:54`). No hidden `_replyto` input was added, so
  the no-JS path can never post an empty Reply-To. The grep showed no other code (check_site,
  build_static, thank-you page) that reads the old `email` name.
- **XSS / prefill:** the prefill code is unchanged. Query values go only into form `.value`
  (`category`, `details`, `comments`). The "You're enquiring about" card, heading and title are
  built with `textContent` / `replaceChildren` from the server's `data.items[key]` lookup, never
  from the raw query string, and the icon selector uses `CSS.escape`. No `|safe` or `innerHTML`
  is used on visitor data. (`innerHTML` is only used to restore the button's own label, which is
  server-rendered markup.) The tester's injection probes confirmed this.
- **Privacy page:** "What we collect" now matches what the forms collect. Required: name and mobile.
  Optional: email, company, area and preferred visit time. Plus what the enquiry is about, details
  and comments. The date is updated.
- **No-JS path:** the form still posts to FormSubmit with `_next`, and the browser checks
  `required`/`pattern`. The date box is visible without JS (it is only hidden by JS, and
  `[hidden]` is `display:none !important`, so the `.form-field` grid can't override it). The
  option values are readable text.
- **Accessibility:** a fieldset/legend groups Day, Time and Date, and `aria-describedby` points to
  the note. Every control has a `<label for>`. The required `*` is `aria-hidden`, and the
  browser's own validation names the field and moves focus to it. The tester checked keyboard order
  and the accessibility tree. A real screen reader was not run (see Notes).
- **Research backlog doc** (`docs/work/2026-11-16-hvac-website-research/01-requirements.md`): it is
  research text and public website names only. It contains no secrets, keys, IP addresses,
  personal emails or phone numbers.
- **Static build / check_site:** both pass (above).

## Findings
1. [nit] `docs/work/2026-11-16-hvac-website-research/01-requirements.md` — this is a separate
   research task's doc, committed in `03ceabd` with this feature. It is harmless, because it is
   only docs, it is where N1 comes from, and it contains nothing sensitive. Normally it would go
   in its own commit or PR. No action needed.
2. [nit] `static/js/enquiry.js:103-104` — the date's min/max are set once when the page loads. If a
   visitor leaves the page open past midnight, yesterday stays selectable until they reload.
   The note "we'll call you to confirm" covers this. No action needed.
3. [nit] `static/js/enquiry.js:108` — `syncVisitDate` also runs on the first `pageshow`, right after
   the call on line 105. It does nothing and is harmless.
4. [nit] `templates/product_enquiry.html:144` — the hint `if you chose "Pick a date"` reuses the
   `optional-label` class only for its grey style. This is fine visually. Mentioned only so that
   nobody later treats `.optional-label` as meaning "this field is optional".

## Requirements check
- R1 met: only name, mobile and category are `required`.
- R2 met: Details is optional, and prefill still fills it.
- R3 met: the label reads "Company name (if it's for a business)" and the field is optional.
- R4 met: `type="email"` checks a typed address, an empty email still sends, and `_replyto` is only sent when there is an address.
- R5 met: same characters and 7–24 length, now actually applied in v-mode browsers. The 7-digit look-ahead comes from the owner-requested defect 6.
- R6 met.
- R7 met: owner's choices, min today, max +30 days, Sundays allowed.
- R8 met.
- R9 met.
- R10 met.
- R11 met: CSS bug fixed with `.required-mark`.
- R12 met.
- R13 met: both forms.
- R14 met: includes the real date for Today/Tomorrow (coordinator decision 3).
- R15 met: "Email address" label (coordinator decision 1).
- R16 met.
- R17 met.
- R18 met: prefill code unchanged, checked by the tester for service, product and spare part.
- R19 met: delivery to be confirmed by the post-merge T3 send.
- R20 met.
- R21 met: session storage is still only name, about, type and reference.
- R22 met.
- R23 met.
- R24 met.
- R25 met.
- R26 met: browser validation, plus a custom message for "Pick a date" with no date.
- R27 met.
- R28 met.
- R29 met: `pageshow` with `persisted` resets the button on both forms.
- R30 met: `.*\S.*` name pattern and the digit look-ahead on the mobile field.

The delivery parts of AC4, AC8, AC9 and AC11 move to the deployer's post-merge sends (owner decision). AC5 was accepted by the owner as FormSubmit's normal Reply behaviour.

## Notes for deployment
- **Commit 04 first.** `04-test-report.md` (round 2) is uncommitted in the working tree. The deployer should commit it, staging it by name, together with this review.
- **Privacy date:** `PRIVACY_UPDATED = "16 November 2026"` (`app.py:879`). If the merge happens on a later day, update it in the same PR before merging (02 deployment note).
- **Post-merge real sends (owner-approved, 3, labelled "TEST – please ignore"):** from https://arcooling.in, send T2 again, then T3 and T4, using the stop rule in 02 and 04.
  - T2 (JS, from the Repair page, all fields): check that Reply goes to the given email (AC4) and that the service subject is right (AC8).
  - T3 (no JS, email empty): check that FormSubmit accepts it, the browser lands on /enquiry/thank-you/, and the email has `area`, `visit_day`, `visit_date` and `visit_time` (AC9). This is the only real proof of the no-JS path. **If FormSubmit rejects it, that is grounds for the owner to consider a revert.**
  - T4 (home page contact form, no email): check AC11.
  - Record the times and references so the owner can delete the test emails.
- **Owner-facing behaviour changes worth telling the owner:**
  - The email row "Email" is now "Email address", and the rows are in a new order. This matters if they have inbox rules on the body. The subject is unchanged.
  - Without JS, a visitor who gives an email will not get one-click Reply (accepted trade-off). The address is still in the email.
- **Not checked by anyone yet:** a real screen reader (NVDA/TalkBack) was not run. Only the accessibility tree was checked. Optional for the owner to try on a phone with TalkBack.
- **Known separate issue (not this task):** `templates/privacy.html:48` says the site "has no analytics", but a Google Tag Manager/Analytics tag loads on the pages. This is backlog item N2 and does not block this change, but the privacy page stays inaccurate on that point until N2 is done.
- Live-site safety: no URL changes, `/go/<id>/` untouched, no database or `data/` changes, no new dependencies, and no server restart steps beyond the usual auto-pull.
