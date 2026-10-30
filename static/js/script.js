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

// Menu dropdowns (products, services, spare parts). On desktop they also open on hover
// (CSS); the arrow button opens them on touch screens, with the keyboard and in the phone menu.
const navItems = [...document.querySelectorAll("[data-nav-item]")];

function setDropdown(item, open) {
  item.classList.toggle("is-open", open);
  item.querySelector(".nav-caret").setAttribute("aria-expanded", String(open));
}

navItems.forEach((item) => {
  item.querySelector(".nav-caret").addEventListener("click", () => {
    const open = !item.classList.contains("is-open");
    navItems.forEach((other) => setDropdown(other, other === item && open));
  });
  // After choosing a link, close the dropdown (it would stay open while it has focus).
  item.querySelector(".nav-menu").addEventListener("click", (event) => {
    if (!event.target.closest("a")) return;
    setDropdown(item, false);
    event.target.closest("a").blur();
  });
});

if (navItems.length) {
  document.addEventListener("click", (event) => {
    navItems.forEach((item) => { if (!item.contains(event.target)) setDropdown(item, false); });
  });
  document.addEventListener("keydown", (event) => {
    const item = navItems.find((candidate) => candidate.classList.contains("is-open"));
    if (event.key !== "Escape" || !item) return;
    setDropdown(item, false);
    item.querySelector(".nav-caret").focus();
  });
}

const year = document.querySelector("#year");
if (year) year.textContent = String(new Date().getFullYear());
