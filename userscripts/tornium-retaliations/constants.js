export const DEBUG = true;
export const BASE_URL = DEBUG ? "http://127.0.0.1:5000" : "https://tornium.com";

// Tampermonkey will store data from GM_setValue separately in its userscript storage,
// however TPDA, violentmonkey, and others will store data from GM_setValue in localStorage
GM_setValue("tornium-retaliations:test", "1");
export const clientLocalGM = localStorage.getItem("tornium-retaliations:test") === "1";
