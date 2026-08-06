/**
 * Auth page interactions — password visibility toggle.
 */
document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-password-toggle]").forEach(function (btn) {
        var control = btn.closest(".auth-field__control");
        if (!control) return;
        var input = control.querySelector("input[type='password'], input[type='text']");
        var showIcon = btn.querySelector("[data-icon-show]");
        var hideIcon = btn.querySelector("[data-icon-hide]");
        if (!input) return;

        btn.addEventListener("click", function () {
            var isPassword = input.type === "password";
            input.type = isPassword ? "text" : "password";
            btn.setAttribute("aria-label", isPassword ? "Hide password" : "Show password");
            if (showIcon) showIcon.hidden = isPassword;
            if (hideIcon) hideIcon.hidden = !isPassword;
        });
    });

    var codeInput = document.querySelector(".auth-field__control--code input");
    if (codeInput) {
        codeInput.classList.add("auth-field__input", "auth-field__input--code");
        codeInput.setAttribute("inputmode", "numeric");
        codeInput.setAttribute("autocomplete", "one-time-code");
    }
});
