const menuToggle = document.querySelector(".menu-toggle");
const primaryNav = document.querySelector("#primary-nav");
const mobileNavQuery = window.matchMedia("(max-width: 900px)");

function setMenu(open) {
  menuToggle.setAttribute("aria-expanded", String(open));
  menuToggle.setAttribute("aria-label", open ? "Close navigation" : "Open navigation");
  primaryNav.classList.toggle("is-open", open);
}

if (menuToggle && primaryNav) {
  menuToggle.addEventListener("click", () => {
    setMenu(menuToggle.getAttribute("aria-expanded") !== "true");
  });

  primaryNav.addEventListener("click", (event) => {
    if (event.target.closest("a") && mobileNavQuery.matches) setMenu(false);
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && primaryNav.classList.contains("is-open")) {
      setMenu(false);
      menuToggle.focus();
    }
  });
}

const header = document.querySelector(".site-header");
if (header) {
  const updateHeader = () => header.classList.toggle("is-scrolled", window.scrollY > 8);
  updateHeader();
  window.addEventListener("scroll", updateHeader, { passive: true });
}

const revealItems = document.querySelectorAll(".reveal");
if ("IntersectionObserver" in window) {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add("is-visible");
      observer.unobserve(entry.target);
    });
  }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });

  revealItems.forEach((item, index) => {
    // Stagger siblings in the same grid for a smoother entrance.
    item.style.transitionDelay = `${Math.min(index % 4, 3) * 70}ms`;
    observer.observe(item);
  });
} else {
  revealItems.forEach((item) => item.classList.add("is-visible"));
}

const year = document.querySelector("#year");
if (year) year.textContent = String(new Date().getFullYear());
