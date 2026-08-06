(function () {
  const presetSelect = document.querySelector("[data-brand-preset-select]");
  const primaryInput = document.querySelector("[data-brand-primary]");
  const accentInput = document.querySelector("[data-brand-accent]");
  const swatches = document.querySelectorAll(".brand-color-preview__swatch");

  if (!presetSelect || !primaryInput || !accentInput) {
    return;
  }

  const presetDataEl = document.getElementById("brand-theme-presets-data");
  const presets = presetDataEl ? JSON.parse(presetDataEl.textContent) : {};

  function updateSwatches(primary, accent) {
    if (swatches[0]) {
      swatches[0].style.background = primary;
    }
    if (swatches[1]) {
      swatches[1].style.background = accent;
    }
  }

  function applyPreset(presetKey) {
    const preset = presets[presetKey];
    if (!preset) {
      return;
    }
    primaryInput.value = preset.primary;
    accentInput.value = preset.accent;
    updateSwatches(preset.primary, preset.accent);
  }

  presetSelect.addEventListener("change", function () {
    if (presetSelect.value !== "custom") {
      applyPreset(presetSelect.value);
    }
  });

  primaryInput.addEventListener("input", function () {
    updateSwatches(primaryInput.value, accentInput.value);
    if (presetSelect.value !== "custom") {
      presetSelect.value = "custom";
    }
  });

  accentInput.addEventListener("input", function () {
    updateSwatches(primaryInput.value, accentInput.value);
    if (presetSelect.value !== "custom") {
      presetSelect.value = "custom";
    }
  });

  updateSwatches(primaryInput.value, accentInput.value);
})();
