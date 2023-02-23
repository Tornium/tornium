/*!
 * Color mode toggler for Bootstrap's docs (https://getbootstrap.com/)
 * Copyright 2011-2022 The Bootstrap Authors
 * Licensed under the Creative Commons Attribution 3.0 Unported License.
 */

let storedTheme = localStorage.getItem('theme');

function getPreferredTheme() {
    if (storedTheme) {
        return storedTheme;
    }

    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'custom-dark' : 'light';
}

function setTheme(theme) {
    if (theme === 'auto' && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        document.documentElement.setAttribute('data-bs-theme', 'custom-dark');
        localStorage.setItem("theme", "custom-dark");
    } else {
        document.documentElement.setAttribute('data-bs-theme', theme);
        localStorage.setItem("theme", theme);
    }
}

$(document).ready(function() {
    setTheme(getPreferredTheme());

    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
        if (storedTheme !== 'light' || storedTheme !== 'custom-dark') {
            setTheme(getPreferredTheme());
        }
    });
});