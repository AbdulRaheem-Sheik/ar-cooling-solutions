// Enquiry form for the static site: prefill from the link, send to FormSubmit (which emails
// the enquiry to the AR Cooling inbox as a table), then show the thank-you page.
(() => {
  const form = document.querySelector("[data-enquiry-form]");
  const dataElement = document.getElementById("enquiry-data");
  if (!form || !dataElement) return;

  const data = JSON.parse(dataElement.textContent);
  const params = new URLSearchParams(window.location.search);
  const field = (name) => form.elements.namedItem(name);
  const status = document.getElementById("form-status");

  // ---- Prefill from the Enquire link ----------------------------------------------
  const prefill = { category: "category", product_description: "details", comments: "comments" };
  Object.entries(prefill).forEach(([param, name]) => {
    const value = params.get(param);
    if (value) field(name).value = value;
  });

  const key = ["product", "service", "part"].map((kind) => params.get(kind) && `${kind}:${params.get(kind)}`).find(Boolean);
  const item = key ? data.items[key] : null;

  function enquiryType() {
    if (item) return item.kind === "part" ? "spare" : item.kind;
    return data.categoryTypes[field("category").value] || "general";
  }

  function showVariant() {
    const variant = enquiryType() === "service" ? "service" : "default";
    document.querySelectorAll("[data-variant]").forEach((element) => {
      element.hidden = element.dataset.variant !== variant;
    });
    const labels = { service: "Service enquiry", spare: "Spare part enquiry", product: "Product enquiry", general: "General enquiry" };
    document.getElementById("enquiry-eyebrow").textContent = labels[enquiryType()];
  }

  if (item) {
    const card = document.getElementById("enquiry-selected");
    const media = document.getElementById("enquiry-selected-media");
    card.href = item.url;
    document.getElementById("enquiry-selected-name").textContent = item.name;
    document.getElementById("enquiry-selected-meta").textContent = item.meta || "";
    const showIcon = () => {
      const template = document.querySelector(`template[data-icon="${CSS.escape(item.icon)}"]`);
      if (template) {
        media.replaceChildren(template.content.cloneNode(true));
        media.firstElementChild.setAttribute("aria-label", item.name);
      }
    };
    if (item.image) {
      const image = document.createElement("img");
      image.src = item.image;
      image.alt = item.name;
      image.addEventListener("error", showIcon);   // photo missing: fall back to the icon
      media.append(image);
    } else {
      showIcon();
    }
    card.hidden = false;
    document.getElementById("enquiry-default-icon").hidden = true;

    const title = document.getElementById("enquiry-title");
    const name = document.createElement("em");
    name.textContent = item.name;
    title.replaceChildren("Enquire about ", name);
    document.title = `Enquire about ${item.name} | AR Cooling Solutions`;
  }
  showVariant();
  field("category").addEventListener("change", showVariant);

  // ---- Preferred visit time ---------------------------------------------------------
  // The date box is only for "Pick a date". It is visible in the HTML so it works without
  // JavaScript; here it is hidden until needed and limited to today .. 30 days ahead.
  const visitDay = field("visit_day");
  const visitTime = field("visit_time");
  const visitDate = field("visit_date");
  const visitDateWrap = form.querySelector("[data-visit-date]");
  const PICK_A_DATE = "Pick a date";

  // YYYY-MM-DD in the visitor's own time zone. toISOString() would use UTC, which in India
  // gives yesterday's date between midnight and 5:30am.
  function isoLocal(date) {
    const pad = (n) => String(n).padStart(2, "0");
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
  }

  function daysFromToday(days) {
    const date = new Date();
    date.setDate(date.getDate() + days);
    return date;
  }

  // A hidden field that is required or out of range would block the form with a message the
  // visitor can't see, so the hidden date is always cleared and made optional.
  function syncVisitDate() {
    const picking = visitDay.value === PICK_A_DATE;
    visitDateWrap.hidden = !picking;
    visitDate.required = picking;
    if (!picking) visitDate.value = "";
    visitDate.setCustomValidity("");
  }

  visitDate.min = isoLocal(new Date());
  visitDate.max = isoLocal(daysFromToday(30));
  syncVisitDate();
  visitDay.addEventListener("change", syncVisitDate);
  // Coming back with the Back button, the browser may restore the old choices.
  window.addEventListener("pageshow", syncVisitDate);
  visitDate.addEventListener("invalid", () => {
    if (visitDate.validity.valueMissing) visitDate.setCustomValidity("Choose a date, or pick another day option.");
  });
  ["input", "change"].forEach((type) => visitDate.addEventListener(type, () => {
    visitDate.setCustomValidity("");
    if (visitDate.value && visitDay.value !== PICK_A_DATE) {
      visitDay.value = PICK_A_DATE;
      syncVisitDate();
    }
  }));

  // e.g. "Tue 17 Nov" (or "Tue 17 Nov 2026" for a picked date).
  function shortDate(date, withYear) {
    const options = { weekday: "short", day: "numeric", month: "short" };
    if (withYear) options.year = "numeric";
    return date.toLocaleDateString("en-IN", options).replace(/,/g, "");
  }

  // One readable line for the email, e.g. "Tomorrow (Tue 17 Nov), Morning (9am–12pm)".
  // Today/Tomorrow get the real date because the team may read the email the next day.
  function visitTimeText() {
    const day = visitDay.value;
    const time = visitTime.value;
    const anyDay = day === "No preference";
    const anyTime = time === "Any time";
    if (anyDay && anyTime) return "Not given";

    let dayText = "Any day";
    if (day === "Today") dayText = `Today (${shortDate(new Date())})`;
    else if (day === "Tomorrow") dayText = `Tomorrow (${shortDate(daysFromToday(1))})`;
    else if (day === PICK_A_DATE && visitDate.value) {
      const [y, m, d] = visitDate.value.split("-").map(Number);
      dayText = shortDate(new Date(y, m - 1, d), true);   // local date, not UTC
    }
    return `${dayText}, ${anyTime ? "any time" : time}`;
  }

  // ---- Submit ---------------------------------------------------------------------
  function makeReference() {
    const now = new Date();
    const pad = (n) => String(n).padStart(2, "0");
    const date = `${String(now.getFullYear()).slice(2)}${pad(now.getMonth() + 1)}${pad(now.getDate())}`;
    return `AR-${date}-${Math.floor(1000 + Math.random() * 9000)}`;
  }

  function showError(message) {
    status.replaceChildren();
    const heading = document.createElement("p");
    heading.textContent = message;
    status.append(heading);
    status.hidden = false;
    status.scrollIntoView({ block: "center", behavior: "smooth" });
  }

  const buttons = form.querySelectorAll('button[type="submit"]');
  const typeLabels = { product: "Product", service: "Service", spare: "Spare part", general: "General" };

  // What FormSubmit receives: its settings (names starting with "_"), then the enquiry as
  // labelled rows in a fixed order, call-back details first. "_template: table" makes the
  // email a two-column table. Empty optional fields say "Not given" so every email has the
  // same rows.
  const orNotGiven = (text) => text || "Not given";

  function emailPayload() {
    const value = (name) => field(name).value.trim();
    const email = value("email_address");
    const payload = {
      _subject: value("_subject"),
      _template: "table",
      _captcha: "false",
      _honey: value("_honey"),   // spam trap: bots fill it, FormSubmit then discards the enquiry
      "Reference": value("reference"),
      "Enquiry type": typeLabels[enquiryType()],
      "Enquiring about": value("enquiring_about"),
      "Name": value("name"),
      "Mobile": value("phone"),
      "Area / locality": orNotGiven(value("area")),
      "Preferred visit time": visitTimeText(),
      "Category": value("category"),
      "Details": orNotGiven(value("details")),
      "Comments": value("comments") || "None",
      // Not called "Email": FormSubmit could take a field by that name for the Reply-To.
      "Email address": orNotGiven(email),
      "Company": orNotGiven(value("company")),
      "Page": value("page_link") || "Enquiry form",
    };
    // "_replyto" makes Reply go straight to the customer. Only sent when there is an
    // address, so the email never gets an empty or "Not given" Reply-To.
    if (email) payload._replyto = email;
    return payload;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!form.reportValidity()) return;

    const reference = makeReference();
    field("reference").value = reference;
    field("enquiry_type").value = enquiryType();
    field("enquiring_about").value = item ? item.name : field("category").value;
    field("page_link").value = item ? data.siteUrl + item.url : "";
    const subjectType = { spare: "spare part" }[enquiryType()] || enquiryType();
    field("_subject").value = `New ${subjectType} enquiry: ${field("enquiring_about").value} (${reference})`;
    // The inbox for this enquiry type (set in ENQUIRY_INBOXES in app.py).
    const endpoint = data.endpoints[enquiryType()] || data.endpoints.general;

    buttons.forEach((button) => { button.disabled = true; });
    status.hidden = true;
    const primary = form.querySelector('button[value="submit"]');
    const primaryLabel = primary.innerHTML;
    primary.textContent = "Sending…";

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(emailPayload()),
      });
      const result = await response.json().catch(() => ({}));
      // FormSubmit answers success as the text "true" (or a boolean).
      const ok = response.ok && String(result.success) === "true";
      if (!ok) throw new Error(result.message || `HTTP ${response.status}`);
    } catch (error) {
      buttons.forEach((button) => { button.disabled = false; });
      primary.innerHTML = primaryLabel;
      showError(`Sorry, your enquiry couldn't be sent (${error.message}). Please try again, or call us on ${data.phone}.`);
      return;
    }

    try {
      sessionStorage.setItem("ar-enquiry", JSON.stringify({
        name: field("name").value.trim(),
        about: field("enquiring_about").value,
        type: enquiryType(),
        reference,
      }));
    } catch {
      // Storage can be blocked; the thank-you page has a generic fallback.
    }
    window.location.href = data.thanksUrl;
  });
})();
