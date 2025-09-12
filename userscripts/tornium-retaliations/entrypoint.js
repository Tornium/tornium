import { torniumFetch } from "./api.js";
import { APP_ID, DEBUG, VERSION } from "./constants.js";
import { log } from "./logging.js";
import { fetchRetaliations } from "./retal.js";
import { resolveToken, isAuthExpired, redirectURI } from "./oauth.js";
import { createSettingsButton, injectSettingsPage, injectSettingsStyles } from "./settings.js";

log(`Loading userscript v${VERSION}${DEBUG ? " with debug" : ""}...`);

if (window.location.pathname.startsWith(`/tornium/${APP_ID}/settings`)) {
    const errorContainer = document.getElementsByClassName("main-wrap")[0];
    const errorContainerTitle = document.getElementById("skip-to-content");

    if (errorContainer == undefined || errorContainerTitle == undefined) {
        log("Failed to load settings page: missing error container");
    } else {
        errorContainer.innerHTML = "";
        errorContainerTitle.innerText = "Tornium Retaliation Settings";

        injectSettingsStyles();
        injectSettingsPage(errorContainer);
    }
} else if (
    window.location.pathname == new URL(redirectURI).pathname &&
    window.location.host == new URL(redirectURI).host
) {
    const callbackParams = new URLSearchParams(window.location.search);
    const callbackState = callbackParams.get("state");
    const callbackCode = callbackParams.get("code");

    const localState = GM_getValue("tornium-retaliations:state");
    const localCodeVerifier = GM_getValue("tornium-retaliations:codeVerifier");
    if (callbackState === localState) {
        resolveToken(callbackCode, callbackState, localCodeVerifier);
    } else {
        unsafeWindow.alert("Invalid security state. Try again.");
        window.location.href = "https://www.torn.com";
    }
} else if (
    window.location.pathname.startsWith("/factions.php") &&
    new URLSearchParams(window.location.search).get("step") == "your"
) {
    createSettingsButton();

    // Identity TTL: one hour
    torniumFetch("user", { ttl: 1000 * 60 * 60 }).then((identityData) => {
        return identityData.factiontid;
    }).then((factionID) => {
        torniumFetch(`faction/${factionID}/attacks/retaliations`).then((retaliations) => {
            console.log(retaliations);
            return retaliations;
        });
        return fetchRetaliations(factionID);
    });
}
