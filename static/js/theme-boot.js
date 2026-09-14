/**
 * Theme boot — apply stored theme before first paint (blocking, no inline script).
 */
(function () {
  var stored = localStorage.getItem("theme");
  var theme = stored || "light";
  if (theme === "system") {
    theme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  document.documentElement.setAttribute("data-theme", theme);
})();
