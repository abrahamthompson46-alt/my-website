/**
 * Navigation — mega menus, mobile drawer, sidebar, header scroll state.
 */
(function () {
  var activeMega = null;

  function closeMegaMenus() {
    document.querySelectorAll("[data-mega-menu]").forEach(function (menu) {
      menu.hidden = true;
    });
    document.querySelectorAll("[data-mega-toggle]").forEach(function (btn) {
      btn.setAttribute("aria-expanded", "false");
    });
    activeMega = null;
  }

  function closeMobileDrawer() {
    var drawer = document.querySelector("[data-mobile-drawer]");
    if (!drawer) return;
    drawer.hidden = true;
    drawer.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
    var toggle = document.querySelector("[data-mobile-nav-toggle]");
    if (toggle) toggle.setAttribute("aria-expanded", "false");
  }

  function openMobileDrawer() {
    var drawer = document.querySelector("[data-mobile-drawer]");
    if (!drawer) return;
    drawer.hidden = false;
    drawer.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
    var toggle = document.querySelector("[data-mobile-nav-toggle]");
    if (toggle) toggle.setAttribute("aria-expanded", "true");
  }

  function initHeaderScroll() {
    var header = document.querySelector("[data-header]");
    if (!header) return;
    window.addEventListener("scroll", function () {
      header.classList.toggle("is-scrolled", window.scrollY > 10);
    }, { passive: true });
  }

  function initSidebar() {
    var layout = document.querySelector(".portal-layout");
    if (!layout) return;

    document.addEventListener("click", function (event) {
      if (event.target.closest("[data-sidebar-open]")) {
        layout.classList.add("is-sidebar-open");
        var backdrop = document.querySelector("[data-sidebar-backdrop]");
        if (backdrop) backdrop.hidden = false;
      }

      if (event.target.closest("[data-sidebar-collapse]")) {
        layout.classList.toggle("is-sidebar-collapsed");
      }

      if (event.target.closest("[data-sidebar-backdrop]")) {
        layout.classList.remove("is-sidebar-open");
        event.target.hidden = true;
      }
    });
  }

  function init() {
    initHeaderScroll();
    initSidebar();

    document.addEventListener("click", function (event) {
      var megaToggle = event.target.closest("[data-mega-toggle]");
      if (megaToggle) {
        var key = megaToggle.getAttribute("data-mega-toggle");
        var menu = document.querySelector('[data-mega-menu="' + key + '"]');
        if (!menu) return;
        var willOpen = menu.hidden;
        closeMegaMenus();
        if (willOpen) {
          menu.hidden = false;
          megaToggle.setAttribute("aria-expanded", "true");
          activeMega = key;
        }
        return;
      }

      if (!event.target.closest(".mega-menu") && !event.target.closest("[data-mega-toggle]")) {
        closeMegaMenus();
      }

      if (event.target.closest("[data-mobile-nav-toggle]")) {
        openMobileDrawer();
        return;
      }

      if (event.target.closest("[data-mobile-drawer-close]")) {
        closeMobileDrawer();
        return;
      }

      var accordion = event.target.closest("[data-mobile-accordion]");
      if (accordion) {
        var panelKey = accordion.getAttribute("data-mobile-accordion");
        var panel = document.querySelector('[data-mobile-accordion-panel="' + panelKey + '"]');
        if (panel) {
          var expanded = accordion.getAttribute("aria-expanded") === "true";
          accordion.setAttribute("aria-expanded", expanded ? "false" : "true");
          panel.hidden = expanded;
        }
      }
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") {
        closeMegaMenus();
        closeMobileDrawer();
        document.querySelectorAll("[data-search-overlay]").forEach(function (el) {
          el.hidden = true;
          el.setAttribute("aria-hidden", "true");
        });
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
