export const DEBUG = false;
export const BASE_URL = DEBUG ? "http://127.0.0.1:5000" : "https://tornium.com";
export const VERSION = "0.1.0-dev";
export const APP_ID = "80698282ed024680b0e3a9439bb764aab4d4d3b27ca087af";
export const APP_SCOPE = "faction:attacks";

// Tampermonkey will store data from GM_setValue separately in its userscript storage,
// however TPDA, violentmonkey, and others will store data from GM_setValue in localStorage
GM_setValue("tornium-retaliations:test", "1");
export const clientLocalGM = localStorage.getItem("tornium-retaliations:test") === "1";
