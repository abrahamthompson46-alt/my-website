/**
 * Checkout manual payment field toggles.
 */
(function () {
  var methodSelect = document.getElementById("id_manual_method");
  var manualFields = document.getElementById("manual-fields");
  if (!methodSelect || !manualFields) return;

  var methodGroups = document.querySelectorAll(".manual-field");

  function syncManualFields() {
    var method = methodSelect.value;
    manualFields.hidden = !method;
    methodGroups.forEach(function (group) {
      var matches = group.classList.contains("manual-field--" + method);
      group.hidden = !method || !matches;
      group.querySelectorAll("input, textarea").forEach(function (input) {
        input.required = matches && input.type !== "file" && input.name !== "notes";
      });
    });
    var proofInput = document.getElementById("id_proof_document");
    if (proofInput) {
      proofInput.required = Boolean(method);
    }
  }

  methodSelect.addEventListener("change", syncManualFields);
  syncManualFields();
})();
