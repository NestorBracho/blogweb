// Loaded in <head>, before the page is drawn, so it never flashes the wrong theme. It lives in a file rather than
// inline because the Content-Security-Policy only allows scripts from the site itself.
const defaultTheme = "dark";
const isToggleEnabled = true;
const userTheme = localStorage.getItem("theme");

function setTheme(mode) {
    if (mode === "dark") {
        document.documentElement.setAttribute("dark", "");
        document.documentElement.classList.add("dark-mode");
    } else if (mode === "light") {
        document.documentElement.removeAttribute("dark");
        document.documentElement.classList.remove("dark-mode");
    }
}

if (isToggleEnabled) {
    if (userTheme) {
        setTheme(userTheme);
    } else {
        setTheme(defaultTheme);
    }
} else {
    setTheme(defaultTheme);
}

if (localStorage.getItem("classView") === "list") {
    document.documentElement.setAttribute("list", "");
    document.documentElement.classList.add('view-list');
}
