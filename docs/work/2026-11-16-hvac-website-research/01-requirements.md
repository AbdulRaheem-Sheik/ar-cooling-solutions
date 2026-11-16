# HVAC website research: new requirements backlog

Research only. Nothing on the website has been changed. This is a ranked list of ideas for
the owner to choose from; each item would go through the normal team process
(requirements, design, build, test) once chosen.

## Goal
Owner's words: "search through Google for HVAC websites, bring the new requirements, and
state them here without any actual work." In short: find out what good AC/HVAC websites do
to win calls and enquiries, compare that with arcooling.in, and list what we should add.

## Users & context
People in Hyderabad who need AC installation, repair, gas refilling, AMC or spare parts,
mostly on phones, often with an AC that has just stopped cooling. Also office, shop and
factory facility managers looking for AMC, commercial HVAC and parts. The site runs on a
free 1 GB server, enquiries go by FormSubmit email, the server stores nothing about visitors,
and the owner edits content through /admin.

---

## 1. What the research says

- **Phone calls are the main lead, so the call button must always be one tap away on a
  phone.** Tap-to-call above the fold plus a sticky call option in the mobile header/footer.
  (topper-digital "what makes an HVAC website convert calls"; smartservice.com "best HVAC
  websites"; scorpion.co)
- **Keep enquiry forms short.** Recommended: about three fields (name, phone, what you
  need). Long forms lose people. (topper-digital; smartservice.com; scorpion.co "offer
  several ways to book")
- **Show proof people can check quickly: reviews, real photos of your own team, years in
  business, warranties/guarantees.** Stock photos and anonymous teams are called out as
  weak. (smartservice.com; topper-digital; scorpion.co; enrichlabs.ai "proof strip")
  Indian booking platforms lead with a service warranty (Urban Company shows a 30-day
  warranty; NoBroker mentions a spare-parts warranty).
- **Google Business Profile and a steady flow of fresh Google reviews matter most for local
  search.** Ask for the review at the end of every job, reply to every review, post photos
  regularly, list each service separately on the profile. (nopio.com; winstondigitalmarketing.com;
  enrichlabs.ai; smartservice.com)
- **Show prices, or at least "starting from" prices, for common jobs.** US guides recommend
  published cost ranges; in India, Urban Company shows starting prices for repair, gas
  refill, installation and service and says the inspection fee is adjusted against the
  repair bill. (smartservice.com; winstondigitalmarketing.com; enrichlabs.ai; urbancompany.com)
- **One good page per service, and area pages only where they are genuinely local.**
  Copy-paste pages with only the area name changed are warned against as "doorway pages".
  (nopio.com; winstondigitalmarketing.com; enrichlabs.ai)
- **Structured data: use HVACBusiness (a LocalBusiness type) with full details, plus FAQ
  and Service markup on service pages.** Google's own LocalBusiness guide requires name and
  address and recommends telephone, url, geo (5 decimal places), opening hours and
  priceRange. Star ratings in markup are not for a business's reviews of itself.
  (developers.google.com LocalBusiness structured data; winstondigitalmarketing.com;
  enrichlabs.ai)
- **Be fast on phones, answer fast, and measure results.** Pages should load in under about
  3 seconds (Google's "good" Core Web Vitals: LCP under 2.5 s, CLS under 0.1). Say how
  quickly you reply, and count calls/WhatsApp/forms separately from visits so you can see
  whether the site actually brings work. (topper-digital; scorpion.co; smartservice.com;
  nopio.com)
- **AMC is a strong repeat-income product if it is explained clearly:** comprehensive (parts
  covered) vs non-comprehensive/service-only, number of visits per year, and what is not
  covered. (onedios.com; scorpion.co "maintenance memberships")

## 2. Already in place on arcooling.in (no need to propose)

- Call button in the header and a sticky **Call + WhatsApp** bar at the bottom of phone
  screens; floating WhatsApp button on larger screens; WhatsApp opens with a pre-filled message.
- 11 service pages with "what's included", "when to book", process steps, FAQs and
  pre-filled enquiry buttons (e.g. /services/repair/ has "Not cooling", "Water leakage" …).
- "Quote before work starts" and "diagnosis charge disclosed at booking" stated clearly.
- AMC page already explains comprehensive vs non-comprehensive and 2–4 visits a year
  (/services/maintenance/).
- Six real customer reviews with Hyderabad localities on the home page.
- Client logos (16) and brand logos (22); "15+ years, 100+ business clients, 25+ brands".
- Working hours (Mon–Sat 9am–7pm), two phone numbers, email, Google Maps link and map.
- SEO basics: page titles, meta descriptions, canonical links, social preview images,
  sitemap.xml and robots.txt, HVACBusiness markup on the home page, FAQ markup on home and
  service pages, visual breadcrumbs.
- Spare-parts catalogue with "check fit & price" enquiry and WhatsApp per part.
- Privacy policy page.

---

## 3. New requirements backlog (ranked by value vs effort)

### N1. Make the main enquiry form quick for home customers — Effort: S
**Why:** Short forms are the most consistent advice (topper-digital, smartservice.com).
Today /enquiry/ requires **Company name** and **Email** as well as name, mobile, category
and details: a homeowner with no company, or no email to hand on a phone, may give up. The
form also asks people to type their area and preferred time inside the message box.
**Requirements**
- R1. On /enquiry/ only name, mobile number and what they need are required; company name and
  email become optional (the home page "Quick enquiry" form likewise makes email optional).
- R2. Add an optional "Area / locality" field and an optional "Preferred visit time"
  (e.g. Today / Tomorrow / Pick a date, and Morning / Afternoon / Evening). These are requests,
  not confirmed bookings, and the page says so.
- R3. The emailed enquiry shows the new fields clearly so the team can call back ready.
- R4. Nothing is stored on the server (still sent by FormSubmit only); the privacy page
  lists any new field.
**Acceptance criteria**
- AC1. On a phone, an enquiry can be sent with only name, mobile and category/details filled in.
- AC2. A test enquiry with area and preferred time arrives in the inbox showing both.
- AC3. Pre-filled service/part enquiries from service and part pages still work.
**Owner input:** confirm the time choices (and whether same-day can be offered).

### N2. Measure calls, WhatsApp taps and enquiries, and fix the privacy page mismatch — Effort: S
**Why:** Guides stress judging the site by leads, not visits (topper-digital, nopio.com).
Finding: every page, including the admin pages, loads a Google Tag Manager container
(`templates/base.html`), while the privacy page says the site "has no analytics". That
statement and the code disagree, which is a trust and data-protection risk.
**Requirements**
- R1. Owner decides: (a) use Google Tag Manager/Analytics to count taps on Call, WhatsApp and
  completed enquiries, or (b) remove the tag. Default proposal: (a), counting taps only, with no
  names, numbers or messages sent to Google.
- R2. The privacy page states truthfully what is measured and by whom, and is updated on the
  same day as the change.
- R3. The tag is not loaded on /admin pages.
- R4. A simple monthly view (in Google Analytics) shows: calls tapped, WhatsApp tapped,
  enquiries sent, by page.
**Acceptance criteria**
- AC1. The privacy page and the site's actual behaviour match (checked in the browser's network tab).
- AC2. A test tap on Call, WhatsApp and a test enquiry each show up in the report the same day.
- AC3. /admin pages load no Google Tag Manager script.
**Owner input:** access to the Google Tag Manager / Analytics account; choice of (a) or (b).

### N3. Google reviews: easy "Review us on Google" link and visible Google rating — Effort: S (site) + ongoing (owner)
**Why:** Fresh Google reviews and a complete Google Business Profile are the top local-search
advice in every SEO source (nopio.com, winstondigitalmarketing.com, enrichlabs.ai,
smartservice.com). The site has a Google Maps link but no "see our Google reviews" or
"leave a review" link.
**Requirements**
- R1. A "Read our Google reviews" link near the home page reviews and on the About page,
  opening the business's Google listing.
- R2. A short, shareable "Review us on Google" link (the profile's own review link) that the
  team can send on WhatsApp after each job; a ready-made message text is provided to the owner.
- R3. If the owner wishes, show the current Google star rating and review count as plain text,
  updated by the owner in /admin (no live connection to Google, no star markup in the code).
**Acceptance criteria**
- AC1. On a phone, the review links open the correct Google listing.
- AC2. The rating text can be changed in /admin and appears on the live site.
**Owner input:** Google Business Profile access/review link; current rating and count.
Owner-side checklist (no website work): primary category "Air conditioning contractor" or
"HVAC contractor", every service listed separately, hours, photos monthly, reply to every review.

### N4. Clear warranty / service guarantee — Effort: S
**Why:** Warranties and guarantees are a standard trust signal (smartservice.com, scorpion.co,
topper-digital); Indian platforms headline them (Urban Company 30-day service warranty,
NoBroker parts warranty). arcooling.in has no warranty statement anywhere (checked home,
/services/repair/, /services/maintenance/, /about/).
**Requirements**
- R1. A short warranty statement shown on the home page "why choose us" area and on each
  relevant service page (repair, gas refilling, installation, compressor, PCB).
- R2. It says what is covered, for how long, and what is not (e.g. new faults, misuse,
  manufacturer warranty on parts handled per the brand's terms).
- R3. The text is editable by the owner in /admin.
**Acceptance criteria**
- AC1. The warranty statement appears on the listed pages and matches the owner's wording.
- AC2. Changing the text in /admin updates all pages.
**Owner input:** the actual terms (e.g. "30-day workmanship warranty on repairs and gas
refilling; parts per manufacturer warranty"). Do not publish until the owner confirms.

### N5. "Starting from" prices for common home jobs — Effort: M
**Why:** Recommended by US guides (smartservice.com, winstondigitalmarketing.com,
enrichlabs.ai) and standard in Hyderabad's biggest competitor (Urban Company shows starting
prices and adjusts the inspection fee against the repair). arcooling.in shows no prices at all;
customers comparing on a phone may leave to a site that does.
**Requirements**
- R1. Show "from ₹…" for a short list of common home jobs: diagnosis/visit charge, split AC
  service, deep cleaning, gas refilling (by gas type), installation, uninstallation, AMC per unit per year.
- R2. Each price says what it includes and that the final quote is given before work starts.
- R3. Prices are editable by the owner in /admin; commercial/central HVAC stays "quote after survey".
- R4. State whether the visit charge is adjusted against the repair bill.
**Acceptance criteria**
- AC1. Each listed service page shows its starting price and inclusions.
- AC2. A price changed in /admin shows on the live page.
**Owner input:** the prices and whether to publish them at all.

### N6. Say how fast we respond, and what happens after hours — Effort: S
**Why:** Guides stress fast replies and covering after-hours leads (scorpion.co,
topper-digital; enrichlabs.ai quotes a BrightLocal survey that most people decide within
30 minutes — unverified). Today the site states hours but no reply time, and nothing on
same-day visits or urgent breakdowns.
**Requirements**
- R1. Near every enquiry form and on the thank-you page: "We call back within … during working
  hours; enquiries after 7pm are answered the next working morning."
- R2. If the owner offers same-day or urgent visits, a short "Urgent breakdown? Call now" line
  on the repair and gas-refilling pages and home page.
**Acceptance criteria**
- AC1. The promise appears on /enquiry/, the home page form, and the thank-you page.
**Owner input:** a reply time the team can really keep; whether same-day/urgent/Sunday service exists.

### N7. Fuller business details for Google (structured data) — Effort: S
**Why:** Google's LocalBusiness guide recommends url, geo, telephone, opening hours and
priceRange; SEO guides add areaServed per area and Service markup per service page
(winstondigitalmarketing.com, enrichlabs.ai). Today the home page markup has name, phone,
email, city, hours and social links, but no url, geo, second phone, localities, or markup
on service pages beyond FAQs.
**Requirements**
- R1. Business markup includes website address, map location (latitude/longitude) and the
  areas actually served (list of localities), using the same name/phone as the Google profile.
- R2. Each service page has Service markup naming the service and linking to the business;
  pages with visual breadcrumbs also have breadcrumb markup.
- R3. No star-rating markup for our own reviews (Google does not allow it for a business
  reviewing itself).
**Acceptance criteria**
- AC1. Google's Rich Results Test shows no errors for the home page and two service pages.
- AC2. Name, phone and area exactly match the Google Business Profile.
**Owner input:** list of localities served; confirm the shop location shown on Google Maps.

### N8. Show matching customer reviews on service pages — Effort: S
**Why:** Proof should be next to the decision (smartservice.com, topper-digital). Reviews
exist only on the home page; service pages show logos but no reviews.
**Requirements**
- R1. Each review can be tagged with a service in /admin (e.g. gas leak review → gas refilling).
- R2. A service page shows its tagged reviews (1–3); if none, the section is hidden.
- R3. Only real reviews are shown (sample reviews never go live, as today).
**Acceptance criteria**
- AC1. /services/gas-refilling/ shows the gas-leak review; a service with no tagged review shows none.
**Owner input:** more real reviews over time (with customer permission).

### N9. Real photos and named people — Effort: M
**Why:** Real team, van and job photos beat stock images (smartservice.com, topper-digital,
enrichlabs.ai). The About page has no names, no team or workshop photos, no founding year
(the home page says "15+ years" but About gives no number).
**Requirements**
- R1. About page: owner/founder name and short story, year started, team photo, workshop/parts desk photo.
- R2. Replace generic service photos with own job photos where available (several product
  pages already have own photos).
- R3. Years-in-business figure is the same everywhere.
**Acceptance criteria**
- AC1. About page shows named people and at least 3 own photos; no conflicting years.
**Owner input:** photos (phone photos are fine), names, founding year, any certificates
(e.g. brand service authorisations, GST registration if the owner wants it shown).

### N10. AMC plans side by side, with price per unit — Effort: M
**Why:** AMC brings repeat income (scorpion.co) and Indian customers compare comprehensive vs
service-only plans (onedios.com). /services/maintenance/ already explains the two types but
has no comparison table, no exclusions list and no price.
**Requirements**
- R1. A simple comparison table: visits per year, cleaning, gas top-up, parts covered,
  breakdown priority, exclusions, "from ₹… per unit per year".
- R2. "Get an AMC quote" asks only for number and type of ACs plus home/office.
**Acceptance criteria**
- AC1. The table reads well on a phone without sideways scrolling.
**Owner input:** what each plan covers, exclusions, prices.

### N11. Check and improve phone speed — Effort: M
**Why:** Every source asks for fast mobile pages (under ~3 s; Google "good": LCP < 2.5 s,
CLS < 0.1, INP < 200 ms). Speed could not be measured during this research (Google
PageSpeed Insights returned "too many requests"). The site loads Google Fonts and Google Tag
Manager from outside, and a map on pages with the contact section.
**Requirements**
- R1. Measure home, /services/repair/, /products/ and /parts/ on mobile in PageSpeed Insights
  and record the results in the task folder.
- R2. Fix whatever pushes a page outside the "good" range, without heavy tools on the server.
**Acceptance criteria**
- AC1. All four pages score "good" for LCP and CLS on mobile in PageSpeed Insights (lab), or
  the remaining gap is explained.
**Owner input:** none.

### N12. "Areas we serve" section, then a few genuine locality pages — Effort: L
**Why:** Area pages help local search only if they are genuinely local; copy-paste pages are
warned against (nopio.com, winstondigitalmarketing.com, enrichlabs.ai). The site names no
localities except in reviews.
**Requirements**
- R1. Step 1 (small): an "Areas we serve" list on the home and contact sections (e.g.
  Kukatpally, Madhapur, Gachibowli, Secunderabad…), matching the Google profile.
- R2. Step 2 (only with real material): a page for a locality only when there are real jobs,
  photos or reviews from it; no page that differs only by area name.
**Acceptance criteria**
- AC1. The areas list matches the owner's list and the structured data (N7).
- AC2. Every locality page has at least one real job/review/photo unique to that area.
**Owner input:** areas actually covered; job photos/reviews per area.

---

## 4. Recommended first 3

1. **N1 Quicker enquiry form** – small change, removes the biggest barrier for home customers on phones.
2. **N2 Measurement + privacy fix** – the privacy page currently says "no analytics" while a Google tag
   loads on every page; fixing it removes a risk and lets the owner see which pages bring calls.
3. **N3 Google reviews links** – the most repeated local-search advice, almost no build work,
   and the owner can start collecting reviews from the next job.

(N4 warranty and N6 response time are also small; they only need the owner's wording.)

## Out of scope
- Live online booking calendar with confirmed slots, online payment, chatbots and financing
  widgets: these need a database of bookings or paid services, conflict with "no visitor data
  on the server", and suit a staffed dispatch desk more than this business.
- Blog / content marketing programme.
- Changing any existing page address.

## Risks
- **Data protection:** new form fields and any analytics must be reflected on the privacy page
  the same day (India DPDP Act; the page already names the Data Protection Board).
- **Publishing prices/warranty** commits the business; owner must approve exact wording.
- **Search ranking:** keep all current URLs; avoid thin locality pages (could be filtered out).
- **1 GB server:** all items are text/markup/images; no new background services.
- **Admin edits:** new editable items (prices, warranty, rating text, review tags) must not
  overwrite content the owner has already edited on the live database.

## Open questions (with proposed defaults)
1. Analytics: count taps with Google Analytics, or remove the Google tag? — Default: count taps only, update privacy page.
2. Publish starting prices? — Default: yes, for 5–7 common home jobs; commercial stays "quote after survey".
3. Warranty terms? — Default to propose: 30 days on repair/gas-refill workmanship, parts as per manufacturer.
4. Reply-time promise? — Default: "call back within 1 working hour".
5. Same-day / urgent / Sunday service offered? — Default: say nothing until confirmed.
6. Google Business Profile access and the review link — needed for N3 and N7.

## Caveats about the research
- Most sources are US marketing agencies that sell websites/SEO (Topper Digital, Scorpion,
  Enrich Labs, Smart Service, Nopio, Winston). Their statistics are mostly unsourced or
  self-reported (e.g. Scorpion's "57% more leads"); none are relied on here. Requirements are
  based only on advice that several independent sources repeat.
- US advice on financing, licences (NATE/BBB) and heating seasons does not apply to Hyderabad
  and was left out.
- Four of the suggested sources could not be read (simprogroup.com, cyberoptik.net, seo.com,
  ciwebgroup.com returned "403 Forbidden"); Google PageSpeed Insights returned "429 too many
  requests", so phone speed is unmeasured.
- Indian references (Urban Company, OneDios, NoBroker blog) are themselves promotional; they
  are used only to show what Hyderabad customers are used to seeing (starting prices,
  warranty, slot choice, AMC types).
- Google's developer documentation is the only authoritative source used; the note that star
  markup is not allowed for a business's own reviews comes from Google's review-snippet
  guidelines linked from that page.
