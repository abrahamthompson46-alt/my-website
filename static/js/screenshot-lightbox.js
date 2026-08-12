/**
 * Click-to-zoom lightbox for product screenshot galleries.
 */
(function () {
  function init() {
    var lightbox = document.querySelector("[data-screenshot-lightbox]");
    if (!lightbox) return;

    var image = lightbox.querySelector("[data-screenshot-lightbox-image]");
    var caption = lightbox.querySelector("[data-screenshot-lightbox-caption]");
    var backdrop = lightbox.querySelector(".screenshot-lightbox__backdrop");
    var lastTrigger = null;

    function open(trigger) {
      var src = trigger.getAttribute("data-lightbox-src");
      if (!src || !image) return;

      lastTrigger = trigger;
      image.src = src;
      image.alt = trigger.getAttribute("data-lightbox-alt") || "";

      if (caption) {
        var text = trigger.getAttribute("data-lightbox-caption") || "";
        caption.textContent = text;
        caption.hidden = !text;
      }

      lightbox.hidden = false;
      document.body.style.overflow = "hidden";

      var closeBtn = lightbox.querySelector("[data-screenshot-lightbox-close]");
      if (closeBtn) closeBtn.focus();
    }

    function close() {
      lightbox.hidden = true;
      document.body.style.overflow = "";
      if (image) {
        image.removeAttribute("src");
        image.alt = "";
      }
      if (lastTrigger) {
        lastTrigger.focus();
        lastTrigger = null;
      }
    }

    document.addEventListener("click", function (event) {
      var trigger = event.target.closest("[data-screenshot-lightbox-open]");
      if (trigger) {
        event.preventDefault();
        open(trigger);
        return;
      }

      if (event.target.closest("[data-screenshot-lightbox-close]") || event.target === backdrop) {
        close();
      }
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && !lightbox.hidden) {
        close();
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
