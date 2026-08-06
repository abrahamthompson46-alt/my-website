document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-seed-form]").forEach(function (form) {
        form.addEventListener("submit", function () {
            var btn = form.querySelector(".control-seed-form__submit, .control-seed-card__btn[type='submit']");
            if (btn) {
                btn.disabled = true;
                btn.classList.add("is-loading");
                if (btn.querySelector(".btn__label")) {
                    btn.querySelector(".btn__label").textContent = "Running…";
                } else {
                    btn.textContent = "Running…";
                }
            }
        });
    });
});
