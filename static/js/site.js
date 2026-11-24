// The main site's script (templates/site.html): only the theme toggle. Everything else works without JavaScript,
// so without it the toggle stays hidden. setTheme, readSetting and saveSetting come from theme.js, loaded first.
document.addEventListener("DOMContentLoaded", function () {
    "use strict";

    const toggle = document.querySelector(".site-theme");
    if (!toggle) {
        return;
    }

    function isDark() {
        return document.documentElement.hasAttribute("dark");
    }

    // The button says what it does: the theme it switches to
    function label() {
        toggle.textContent = isDark() ? toggle.dataset.labelLight : toggle.dataset.labelDark;
    }

    toggle.addEventListener("click", function () {
        const theme = isDark() ? "light" : "dark";
        setTheme(theme);
        saveSetting("theme", theme);
        label();
    });

    label();
    toggle.hidden = false;
});
