/**
 * Theme switcher — light / dark / system preference.
 */
(function () {
  var STORAGE_KEY = "theme";

  function resolveTheme(preference) {
    if (preference === "system") {
      return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }
    return preference === "dark" ? "dark" : "light";
  }

  function applyTheme(preference) {
    var resolved = resolveTheme(preference);
    document.documentElement.setAttribute("data-theme", resolved);
    localStorage.setItem(STORAGE_KEY, preference);
    syncControls(preference, resolved);
  }

  function syncControls(preference, resolved) {
    document.querySelectorAll("[data-theme-switcher]").forEach(function (root) {
      root.querySelectorAll("[data-theme-value]").forEach(function (btn) {
        btn.setAttribute("aria-pressed", btn.getAttribute("data-theme-value") === preference ? "true" : "false");
      });
    });
    document.querySelectorAll("[data-theme-toggle]").forEach(function (btn) {
      btn.setAttribute("aria-label", resolved === "dark" ? "Switch to light mode" : "Switch to dark mode");
    });
  }

  function init() {
    var stored = localStorage.getItem(STORAGE_KEY) || "light";
    applyTheme(stored);

    document.addEventListener("click", function (event) {
      var valueBtn = event.target.closest("[data-theme-value]");
      if (valueBtn) {
        applyTheme(valueBtn.getAttribute("data-theme-value"));
        return;
      }

      var toggleBtn = event.target.closest("[data-theme-toggle]");
      if (toggleBtn) {
        var current = localStorage.getItem(STORAGE_KEY) || "light";
        var resolved = resolveTheme(current);
        applyTheme(resolved === "dark" ? "light" : "dark");
      }
    });

    window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", function () {
      if ((localStorage.getItem(STORAGE_KEY) || "light") === "system") {
        applyTheme("system");
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  window.applyTheme = applyTheme;
})();
