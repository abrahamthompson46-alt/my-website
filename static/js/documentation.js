/**
 * Documentation sidebar toggle for mobile.
 */
(function () {
  var layout = document.querySelector(".docs-layout");
  var backdrop = document.querySelector("[data-docs-sidebar-backdrop]");
  var openBtn = document.querySelector("[data-docs-sidebar-open]");

  if (!layout) return;

  function closeSidebar() {
    layout.classList.remove("is-sidebar-open");
    if (backdrop) backdrop.hidden = true;
    document.body.style.overflow = "";
  }

  function openSidebar() {
    layout.classList.add("is-sidebar-open");
    if (backdrop) backdrop.hidden = false;
    document.body.style.overflow = "hidden";
  }

  if (openBtn) {
    openBtn.addEventListener("click", openSidebar);
  }

  if (backdrop) {
    backdrop.addEventListener("click", closeSidebar);
  }
})();
