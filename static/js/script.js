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

const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

// Counters below the home hero: count up from 0 the first time they scroll into view.
// The real number is already in the page, so without JavaScript (or with reduced motion) it just shows.
const counters = document.querySelectorAll("[data-count-to]");
if (counters.length && "IntersectionObserver" in window && !prefersReducedMotion) {
  const format = (n) => n.toLocaleString("en-IN");
  const countUp = (element) => {
    const target = Number(element.dataset.countTo);
    const start = performance.now();
    const step = (now) => {
      const t = Math.min((now - start) / 1600, 1);
      element.textContent = format(Math.round(target * (1 - (1 - t) ** 3)));   // ease-out
      if (t < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  };
  const counterObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      countUp(entry.target);
      counterObserver.unobserve(entry.target);
    });
  }, { threshold: 0.6 });
  counters.forEach((element) => {
    element.textContent = "0";
    counterObserver.observe(element);
  });
}

// Reviews carousel: a scroll-snap row (swipe on phones) with arrows, dots and auto-slide.
// Auto-slide pauses while the pointer or keyboard focus is inside, and is off for reduced motion.
document.querySelectorAll("[data-carousel]").forEach((carousel) => {
  const track = carousel.querySelector("[data-carousel-track]");
  const cards = [...track.children];
  const dots = carousel.querySelector("[data-carousel-dots]");
  const perView = () => Math.max(1, Math.round(track.clientWidth / cards[0].getBoundingClientRect().width));
  const pageCount = () => Math.ceil(cards.length / perView());
  const currentPage = () => Math.round(track.scrollLeft / track.clientWidth);

  const goTo = (page) => {
    const total = pageCount();
    const target = cards[((page % total) + total) % total * perView()];
    track.scrollTo({ left: target.offsetLeft - track.offsetLeft, behavior: prefersReducedMotion ? "auto" : "smooth" });
  };

  const renderDots = () => {
    dots.replaceChildren(...Array.from({ length: pageCount() }, (_, page) => {
      const dot = document.createElement("button");
      dot.type = "button";
      dot.className = "carousel-dot";
      dot.setAttribute("aria-label", `Show reviews ${page + 1} of ${pageCount()}`);
      dot.addEventListener("click", () => goTo(page));
      return dot;
    }));
    updateDots();
  };
  const updateDots = () => {
    [...dots.children].forEach((dot, page) => dot.setAttribute("aria-current", String(page === currentPage())));
  };

  carousel.querySelector("[data-carousel-prev]").addEventListener("click", () => goTo(currentPage() - 1));
  carousel.querySelector("[data-carousel-next]").addEventListener("click", () => goTo(currentPage() + 1));
  track.addEventListener("scroll", () => requestAnimationFrame(updateDots), { passive: true });
  window.addEventListener("resize", renderDots, { passive: true });
  renderDots();

  if (prefersReducedMotion) return;
  let paused = false;
  const pause = () => { paused = true; };
  const resume = () => { paused = false; };
  carousel.addEventListener("pointerenter", pause);
  carousel.addEventListener("pointerleave", resume);
  carousel.addEventListener("focusin", pause);
  carousel.addEventListener("focusout", resume);
  track.addEventListener("touchstart", pause, { passive: true });
  setInterval(() => {
    if (!paused && !document.hidden) goTo(currentPage() + 1);
  }, 5500);
});

