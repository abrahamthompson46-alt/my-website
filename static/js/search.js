/**
 * Search overlay and inline search helpers.
 */
(function () {
  function openSearch() {
    var overlay = document.querySelector("[data-search-overlay]");
    if (!overlay) return;
    overlay.hidden = false;
    overlay.setAttribute("aria-hidden", "false");
    var input = overlay.querySelector(".search-bar__input");
    if (input) input.focus();
    document.body.style.overflow = "hidden";
  }

  function closeSearch() {
    var overlay = document.querySelector("[data-search-overlay]");
    if (!overlay) return;
    overlay.hidden = true;
    overlay.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
  }

  function init() {
    document.addEventListener("click", function (event) {
      if (event.target.closest("[data-search-open]")) {
        openSearch();
        return;
      }
      if (event.target.closest("[data-search-close]")) {
        closeSearch();
      }
      if (event.target.closest("[data-search-clear]")) {
        var bar = event.target.closest(".search-bar");
        var input = bar && bar.querySelector(".search-bar__input");
        if (input) {
          input.value = "";
          input.focus();
        }
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  window.openSearch = openSearch;
  window.closeSearch = closeSearch;
})();
