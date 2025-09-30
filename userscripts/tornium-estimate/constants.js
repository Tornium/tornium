export const DEBUG = false;
export const BASE_URL = DEBUG ? "http://127.0.0.1:5000" : "https://tornium.com";
export const VERSION = "1.0.0-dev";
export const APP_ID = "6be7696c40837f83e5cab139e02e287408c186939c10b025";
export const APP_SCOPE = "identity api_key:usage";

// Tampermonkey will store data from GM_setValue separately in its userscript storage,
// however TPDA, violentmonkey, and others will store data from GM_setValue in localStorage
GM_setValue("tornium-estimate:test", "1");
export const clientLocalGM = localStorage.getItem("tornium-estimate:test") === "1";
