// Quick enquiry form in the contact section: send to FormSubmit (which emails it to the
// AR Cooling inbox as a table), then show the thank-you page. Same flow as enquiry.js.
(() => {
  const form = document.querySelector("[data-contact-form]");
  if (!form) return;

  const field = (name) => form.elements.namedItem(name);
  const value = (name) => field(name).value.trim();
  const status = form.querySelector("[data-contact-status]");
  const button = form.querySelector('button[type="submit"]');
  const label = button.innerHTML;

  // After a send, Back can bring this page out of the browser's cache exactly as it was left:
  // button disabled and saying "Sending…". Make it usable again.
  window.addEventListener("pageshow", (event) => {
    if (!event.persisted) return;
    button.disabled = false;
    button.innerHTML = label;
  });

  const typeKeys = { Service: "service", Product: "product", "Spare part": "spare" };

  function makeReference() {
    const now = new Date();
    const pad = (n) => String(n).padStart(2, "0");
    const date = `${String(now.getFullYear()).slice(2)}${pad(now.getMonth() + 1)}${pad(now.getDate())}`;
    return `AR-${date}-${Math.floor(1000 + Math.random() * 9000)}`;
  }

  // Count the sent enquiry in Google Analytics, then open the thank-you page. Waits for
  // Google at most 1 second, and not at all if the Google tag didn't load (blocked, slow).
  // Only fixed words are sent, never what the visitor typed. Twin: enquiry.js.
  function countEnquiryThenGo(url, details) {
    let gone = false;
    const go = () => { if (!gone) { gone = true; window.location.href = url; } };
    if (typeof gtag !== "function" || !window.google_tag_manager) return go();
    gtag("event", "enquiry_sent", { ...details, event_callback: go, event_timeout: 1000 });
    setTimeout(go, 1000);   // the real guarantee: event_callback may never come through GTM
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!form.reportValidity()) return;

    const reference = makeReference();
    const topic = value("topic");
    const email = value("email_address");
    const payload = {
      _subject: `New enquiry from the contact section: ${topic} (${reference})`,
      _template: "table",
      _captcha: "false",
      _honey: value("_honey"),
      "Reference": reference,
      "Enquiry type": "Quick enquiry",
      "Looking for": topic,
      "Name": value("name"),
      // Not called "Email": FormSubmit could take a field by that name for the Reply-To.
      "Email address": email || "Not given",
      "Mobile": value("phone"),
      "Message": value("message"),
      "Page": window.location.href,
    };
    // Reply goes straight to the customer, but only when they gave an address: an empty or
    // "Not given" Reply-To would be broken.
    if (email) payload._replyto = email;

    button.disabled = true;
    status.hidden = true;
    button.textContent = "Sending…";

    try {
      const response = await fetch(form.dataset.endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(payload),
      });
      const result = await response.json().catch(() => ({}));
      if (!(response.ok && String(result.success) === "true")) throw new Error(result.message || `HTTP ${response.status}`);
    } catch (error) {
      button.disabled = false;
      button.innerHTML = label;
      const message = document.createElement("p");
      message.textContent = `Sorry, your enquiry couldn't be sent (${error.message}). Please try again, or call us on ${form.dataset.phone}.`;
      status.replaceChildren(message);
      status.hidden = false;
      return;
    }

    try {
      sessionStorage.setItem("ar-enquiry", JSON.stringify({
        name: value("name"),
        about: topic === "Other" ? "" : topic,
        type: typeKeys[topic] || "general",
        reference,
      }));
    } catch {
      // Storage can be blocked; the thank-you page has a generic fallback.
    }
    // topic is one of the form's own fixed choices, mapped to four fixed words. The own-key
    // test means even a tampered value like "toString" can only give "general" (and works on
    // older phones, unlike Object.hasOwn).
    const countedType = Object.prototype.hasOwnProperty.call(typeKeys, topic) ? typeKeys[topic] : "general";
    countEnquiryThenGo(form.dataset.thanksUrl, { enquiry_form: "quick", enquiry_type: countedType });
  });
})();
