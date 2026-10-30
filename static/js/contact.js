// Quick enquiry form in the contact section: send to FormSubmit (which emails it to the
// AR Cooling inbox as a table), then show the thank-you page. Same flow as enquiry.js.
(() => {
  const form = document.querySelector("[data-contact-form]");
  if (!form) return;

  const field = (name) => form.elements.namedItem(name);
  const value = (name) => field(name).value.trim();
  const status = form.querySelector("[data-contact-status]");
  const button = form.querySelector('button[type="submit"]');
  const typeKeys = { Service: "service", Product: "product", "Spare part": "spare" };

  function makeReference() {
    const now = new Date();
    const pad = (n) => String(n).padStart(2, "0");
    const date = `${String(now.getFullYear()).slice(2)}${pad(now.getMonth() + 1)}${pad(now.getDate())}`;
    return `AR-${date}-${Math.floor(1000 + Math.random() * 9000)}`;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!form.reportValidity()) return;

    const reference = makeReference();
    const topic = value("topic");
    const payload = {
      _subject: `New enquiry from the contact section: ${topic} (${reference})`,
      _template: "table",
      _captcha: "false",
      _replyto: value("email"),
      _honey: value("_honey"),
      "Reference": reference,
      "Enquiry type": "Quick enquiry",
      "Looking for": topic,
      "Name": value("name"),
      "Email": value("email"),
      "Mobile": value("phone"),
      "Message": value("message"),
      "Page": window.location.href,
    };

    button.disabled = true;
    status.hidden = true;
    const label = button.innerHTML;
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
    window.location.href = form.dataset.thanksUrl;
  });
})();
