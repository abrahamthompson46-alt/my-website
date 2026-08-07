/**
 * Homepage scroll reveal — respects prefers-reduced-motion.
 */
(function () {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  function init() {
    var sections = document.querySelectorAll(
      ".home-products, .home-why, .home-industries, .home-testimonials, .home-news, .home-cta, .home-partners, .home-demo, .home-newsletter"
    );

    sections.forEach(function (el) {
      el.classList.add("home-reveal");
    });

    if (!("IntersectionObserver" in window)) {
      sections.forEach(function (el) { el.classList.add("is-visible"); });
      return;
    }

    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
    );

    sections.forEach(function (el) { observer.observe(el); });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  if (window.location.hash) {
    var target = document.querySelector(window.location.hash);
    if (target) {
      window.requestAnimationFrame(function () {
        target.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    }
  }
})();
