// Loaded in <head>, before the page is drawn, so it never flashes the wrong theme. It lives in a file rather than
// inline because the Content-Security-Policy only allows scripts from the site itself.
const defaultTheme = "dark";

// The browser can refuse local storage (blocked site data, some private windows) and throw: then nothing is
// remembered, and the page still works. common.js saves the choices with these too.
function readSetting(key) {
    try {
        return localStorage.getItem(key);
    } catch (error) {
        return null;
    }
}

function saveSetting(key, value) {
    try {
        if (value === null) {
            localStorage.removeItem(key);
        } else {
            localStorage.setItem(key, value);
        }
    } catch (error) {
        // Not remembered for the next page, which is all
    }
}

function setTheme(mode) {
    if (mode === "dark") {
        document.documentElement.setAttribute("dark", "");
        document.documentElement.classList.add("dark-mode");
    } else if (mode === "light") {
        document.documentElement.removeAttribute("dark");
        document.documentElement.classList.remove("dark-mode");
    }
}

setTheme(readSetting("theme") || defaultTheme);

if (readSetting("classView") === "list") {
    document.documentElement.setAttribute("list", "");
    document.documentElement.classList.add('view-list');
}
