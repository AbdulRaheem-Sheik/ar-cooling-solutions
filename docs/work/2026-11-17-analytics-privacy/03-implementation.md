# Implementation: Count calls, WhatsApp taps and enquiries, and fix the privacy mismatch (Option A)

## Summary
Option A built as designed. Public pages keep the Google tag. The snippet in `base.html` is
unchanged; only its comment is new. The three admin templates no longer load the Google tag
or `script.js`, so nothing on an admin page can send data to Google. A new `enquiry_sent`
event fires only after FormSubmit confirms a send. It is sent from a small
`countEnquiryThenGo` helper that keeps the thank-you redirect to 1 second at most, and
redirects straight away if the Google tag didn't load. The privacy page now describes Google
Analytics honestly and has a new date. The footer link reads "Privacy & cookies".
`check_site.py` gets new local and `--live` checks that stop the tag from coming back on
admin pages and stop the privacy text drifting from what the site does.

## Files changed
| File | Change |
|---|---|
| `templates/admin_login.html`, `admin_dashboard.html`, `admin_edit.html` | Removed the `<!-- Google tag -->` comment, both snippet `<script>` tags and the `script.js` include (old lines 4–11). Fonts and `style.css` unchanged. |
| `templates/base.html` | Snippet byte-for-byte unchanged; its comment now explains why it is public-only and points to the check and `/privacy/`. Footer link text `Privacy policy` → `Privacy &amp; cookies` (same `url_for('privacy')`). |
| `static/js/script.js` | Comment above the click tracker only (public pages only; `link_text` is our own link text, never typed text). No behaviour change. |
| `static/js/enquiry.js` | Added `countEnquiryThenGo(url, details)` and `countedType()` (enquiry type limited to `product`/`service`/`spare`/`general`). Success path now calls `countEnquiryThenGo(data.thanksUrl, { enquiry_form: "full", enquiry_type: countedType() })` instead of setting `location.href`. Failure and validation paths untouched. |
| `static/js/contact.js` | Same helper (twin). Success path calls `countEnquiryThenGo(form.dataset.thanksUrl, { enquiry_form: "quick", enquiry_type: countedType })`, where `countedType` maps the topic through `typeKeys` with an own-key test, falling back to `general`. |
| `templates/privacy.html` | "What we collect" opening reworded; "We do count visits…" sentence added; new section "Visitor statistics (Google Analytics)" (draft wording from the design, including the 14-month sentence); the "has no analytics" item replaced by "The only cookies are the Google Analytics ones described above. We don't use advertising cookies."; session-storage and Google Fonts items unchanged. All external links `target="_blank" rel="noopener noreferrer"`. |
| `app.py` | `PRIVACY_UPDATED = "17 November 2026"`. |
| `tools/check_site.py` | `GOOGLE_TAG`, `TRACKING_MARKERS`, `tag_count()`, `tracking_found()`. New checks: public pages + 404 load the tag exactly once; privacy page has "Google Analytics" and not "has no analytics"; admin login/dashboard/edit have no marker; dashboard links to an edit page (so the edit page check can't be skipped without failing); `--live`: home has the tag once, `/admin/login` has none. Docstring updated. |

## Requirements covered
| Req | Where / how |
|---|---|
| S1 | No server-side change apart from the date constant. No storage, logging or cookies from our code. |
| S2 | No new packages. |
| S3 | No URL changes. The footer link keeps `/privacy/`. |
| S4 / A1 | Admin templates have no tag and no `script.js`; `check_admin` checks this ("admin pages load no Google tag (3 checked)"). |
| S5 / A6 | `privacy.html` rewrite, `PRIVACY_UPDATED`, plus a consistency check. |
| S6 | `check_site.py` new checks; full run passes (build included). |
| S7 | Form fetch / failure / no-JS paths unchanged; redirect happens at once if GTM isn't loaded. |
| A2 / A3 | `call_click` / `whatsapp_click` / `email_click` code unchanged (comment only). |
| A4 | `enquiry_sent` only on the FormSubmit-success path, after the `sessionStorage` block; ≤ 1 s wait (`event_timeout` + `setTimeout`), single redirect guarded by `gone`. |
| A5 | Only `enquiry_form` (`full`/`quick`) and `enquiry_type` (fixed list of four) are sent. |
| A7 | No banner; footer link "Privacy & cookies". |
| A8 | Owner steps are in 02-design (Deployment notes). Not code; the deployer turns them into owner notes. |
| A9 | Snippet unchanged (owner step 0 confirmed events arrive). |

## Deviations from design
1. **Quick form type mapping uses an own-key test**
   (`Object.prototype.hasOwnProperty.call(typeKeys, topic)`) instead of
   `typeKeys[topic] || "general"`. Otherwise a tampered topic like `toString` would have
   returned a function rather than one of the four words. I used `hasOwnProperty` instead of
   `Object.hasOwn` because `Object.hasOwn` throws on older iPhones (Safari < 15.4), and that
   would block the redirect.
2. **The full form's type filter is named `countedType()`** (the design called it `safeType`).
   It checks `enquiryType()` against `["product","service","spare","general"]`.
3. **Extra check: "dashboard links to an edit page".** Before this, if the edit link was
   missing, the edit-page checks were skipped without any failure. Now the admin no-tag check
   cannot quietly cover only 2 pages.
4. **The 14-month retention sentence is included.** The coordinator accepted Q3, and the owner
   must set GA4 retention to 14 months before merge.
5. **"Visitor statistics"** in the "We do count visits" sentence uses `<i>` for the
   design's *italic*.

## Checks run
- `.venv/Scripts/python tools/check_site.py`: **ALL CHECKS PASSED** (153 pages render; public
  pages load the Google tag exactly once; privacy page explains Google Analytics; admin pages
  load no Google tag (3 checked); static build of 153 pages + 404 with link and sitemap
  checks OK).
- Negative test (temporary edit, then restored from a copy): I put the snippet back into
  `admin_login.html` and put "has no analytics" back into `privacy.html`. Both new checks
  FAILED as expected (`/admin/login: googletagmanager.com, gtag(, dataLayer`). Files
  restored; `git diff` confirmed.
- `--live` logic against a local `serve.py`:
  `check_site.py --skip-build --live --live-url http://127.0.0.1:8080` gave ALL CHECKS PASSED,
  including "live home page loads the Google tag once" and "live /admin/login loads no
  Google tag". The real live site was not checked; it still has the old code until merge.
- Node unit test of `countEnquiryThenGo` (both files, extracted with fake `window`, `gtag` and
  no network). No gtag: redirects at once, no event. gtag but no `google_tag_manager`:
  redirects at once, no event. GTM loaded and the callback fires: one
  `enquiry_sent` event, redirect after about 50 ms. GTM loaded with no callback: one event,
  redirect after about 1 s. The redirect happened exactly once in every case.
- `node --check` on `enquiry.js`, `contact.js`, `script.js`: OK.
- Nothing was sent to FormSubmit or Google Analytics. No browser test was run.

## Commits
- `209360f` Analytics: admin pages stop loading Google, count sent enquiries, honest privacy page

## Rework log
(none yet)
