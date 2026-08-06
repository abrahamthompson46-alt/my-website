/**
 * Modal dialog controller — open/close via data attributes.
 */
(function () {
  var openModalEl = null;

  function getModal(id) {
    return document.getElementById(id);
  }

  function openModal(id) {
    var modal = getModal(id);
    if (!modal) return;
    modal.hidden = false;
    openModalEl = modal;
    document.body.style.overflow = "hidden";
    var focusable = modal.querySelector("button, input, textarea, select, a[href]");
    if (focusable) focusable.focus();
  }

  function closeModal(modal) {
    if (!modal) return;
    modal.hidden = true;
    if (openModalEl === modal) {
      openModalEl = null;
      document.body.style.overflow = "";
    }
  }

  function init() {
    document.addEventListener("click", function (event) {
      var openTrigger = event.target.closest("[data-modal-open]");
      if (openTrigger) {
        openModal(openTrigger.getAttribute("data-modal-open"));
        return;
      }

      if (event.target.closest("[data-modal-close]")) {
        var modal = event.target.closest("[data-modal]");
        closeModal(modal);
      }
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && openModalEl) {
        closeModal(openModalEl);
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  window.openModal = openModal;
  window.closeModal = closeModal;
})();
