/**
 * Global UI behaviors — dismissible alerts, table select-all.
 */
(function () {
  function initDismissibleAlerts() {
    document.addEventListener("click", function (event) {
      var dismiss = event.target.closest(".alert__dismiss");
      if (!dismiss) return;
      var alert = dismiss.closest(".alert");
      if (alert) alert.remove();
    });
  }

  function initTableSelectAll() {
    document.addEventListener("change", function (event) {
      if (!event.target.matches("[data-table-select-all]")) return;
      var table = event.target.closest(".table");
      if (!table) return;
      table.querySelectorAll("tbody .form-check-input").forEach(function (checkbox) {
        checkbox.checked = event.target.checked;
      });
    });
  }

  function init() {
    initDismissibleAlerts();
    initTableSelectAll();
    if (window.renderIcons) window.renderIcons();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
