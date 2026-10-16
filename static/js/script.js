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

// Collapsible catalog categories (products, services, spare parts).
const catalogGroups = [...document.querySelectorAll(".catalog-group")];
const catalogToggles = document.querySelectorAll("[data-catalog-toggle]");

function syncCatalogToggles() {
  const allOpen = catalogGroups.length > 0 && catalogGroups.every((group) => group.open);
  catalogToggles.forEach((button) => {
    button.setAttribute("aria-expanded", String(allOpen));
    button.querySelector(".catalog-toggle-label").textContent = allOpen ? "Collapse all" : "Expand all";
  });
}

// Open the category that holds a #target (a category or a card inside one).
function revealCatalogTarget(hash, scroll) {
  if (!hash || hash === "#") return;
  let target;
  try {
    target = document.querySelector(decodeURIComponent(hash));
  } catch {
    return;
  }
  const group = target && target.closest(".catalog-group");
  if (!group) return;
  group.open = true;
  if (scroll) target.scrollIntoView({ block: "start" });
}

if (catalogGroups.length) {
  catalogGroups.forEach((group) => group.addEventListener("toggle", syncCatalogToggles));
  catalogToggles.forEach((button) => {
    button.addEventListener("click", () => {
      const open = button.getAttribute("aria-expanded") !== "true";
      catalogGroups.forEach((group) => { group.open = open; });
      syncCatalogToggles();
    });
  });

  // Same-page links: open the category before the browser scrolls to it.
  document.addEventListener("click", (event) => {
    const link = event.target.closest('a[href*="#"]');
    if (link && link.pathname === location.pathname) revealCatalogTarget(link.hash, false);
  });
  window.addEventListener("hashchange", () => revealCatalogTarget(location.hash, true));
  revealCatalogTarget(location.hash, true);
  syncCatalogToggles();
}

const year = document.querySelector("#year");
if (year) year.textContent = String(new Date().getFullYear());
