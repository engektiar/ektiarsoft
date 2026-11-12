(function () {
  "use strict";
  const root = document.documentElement;

  // ---- theme toggle (persisted) ----
  document.querySelectorAll("[data-theme-toggle]").forEach((btn) =>
    btn.addEventListener("click", () => {
      const next = root.dataset.theme === "light" ? "dark" : "light";
      root.dataset.theme = next;
      try { localStorage.setItem("theme", next); } catch (e) {}
    })
  );

  // ---- sticky header ----
  const header = document.querySelector(".site-header");
  const toTop = document.querySelector(".to-top");
  const onScroll = () => {
    const y = window.scrollY;
    header && header.classList.toggle("scrolled", y > 10);
    toTop && toTop.classList.toggle("show", y > 600);
  };
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();
  toTop && toTop.addEventListener("click", () => window.scrollTo({ top: 0 }));

  // ---- mobile menu ----
  const menuBtn = document.querySelector(".menu-toggle");
  const links = document.querySelector(".nav-links");
  if (menuBtn && links) {
    const setMenu = (open) => {
      links.classList.toggle("open", open);
      header && header.classList.toggle("menu-open", open);
      menuBtn.setAttribute("aria-expanded", open);
      menuBtn.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    };
    menuBtn.addEventListener("click", (e) => { e.stopPropagation(); setMenu(!links.classList.contains("open")); });
    links.querySelectorAll("a").forEach((a) => a.addEventListener("click", () => setMenu(false)));
    document.addEventListener("click", (e) => { if (!e.target.closest(".site-header")) setMenu(false); });
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") setMenu(false); });
    window.addEventListener("resize", () => { if (window.innerWidth > 900) setMenu(false); });
  }

  // ---- reveal on scroll ----
  const io = new IntersectionObserver(
    (entries) => entries.forEach((e) => {
      if (e.isIntersecting) { e.target.classList.add("in-view"); io.unobserve(e.target); }
    }),
    { threshold: 0.12 }
  );
  document.querySelectorAll(".reveal, .skills").forEach((el) => io.observe(el));
  // safety net: never leave content invisible (slow devices, print, odd scroll containers)
  setTimeout(() => document.querySelectorAll(".reveal:not(.in-view)").forEach((el) => {
    const r = el.getBoundingClientRect();
    if (r.top < window.innerHeight * 1.5) el.classList.add("in-view");
  }), 1200);
  window.addEventListener("beforeprint", () => document.querySelectorAll(".reveal").forEach((el) => el.classList.add("in-view")));

  // ---- counters ----
  const counterIO = new IntersectionObserver((entries) => entries.forEach((e) => {
    if (!e.isIntersecting) return;
    const el = e.target, end = parseInt(el.dataset.count, 10) || 0, t0 = performance.now(), dur = 1600;
    const tick = (t) => {
      const p = Math.min(1, (t - t0) / dur);
      el.textContent = Math.round(end * (1 - Math.pow(1 - p, 3)));
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
    counterIO.unobserve(el);
  }), { threshold: 0.5 });
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!reduceMotion) document.querySelectorAll("[data-count]").forEach((el) => counterIO.observe(el));

  // ---- typing effect ----
  const typed = document.querySelector("[data-typed]");
  if (typed) {
    const words = JSON.parse(typed.dataset.typed);
    let w = 0, i = 0, del = false;
    const loop = () => {
      const word = words[w];
      typed.textContent = word.slice(0, i);
      if (!del && i < word.length) i++;
      else if (del && i > 0) i--;
      else if (!del) { del = true; return setTimeout(loop, 1800); }
      else { del = false; w = (w + 1) % words.length; }
      setTimeout(loop, del ? 45 : 85);
    };
    loop();
  }

  // ---- spotlight cards ----
  document.querySelectorAll(".card-spot").forEach((card) =>
    card.addEventListener("pointermove", (e) => {
      const r = card.getBoundingClientRect();
      card.style.setProperty("--mx", `${e.clientX - r.left}px`);
      card.style.setProperty("--my", `${e.clientY - r.top}px`);
    })
  );

  // ---- portfolio filter ----
  const filterBtns = document.querySelectorAll("[data-filter]");
  filterBtns.forEach((btn) => btn.addEventListener("click", () => {
    filterBtns.forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    const f = btn.dataset.filter;
    document.querySelectorAll("[data-category]").forEach((item) => {
      item.style.display = f === "all" || item.dataset.category === f ? "" : "none";
    });
  }));

  // ---- auto-dismiss alerts ----
  document.querySelectorAll(".alert").forEach((a) => setTimeout(() => {
    a.style.transition = "opacity .4s"; a.style.opacity = "0"; setTimeout(() => a.remove(), 400);
  }, 5000));
})();
