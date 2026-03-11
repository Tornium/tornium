/* Copyright (C) 2021-2025 tiksan

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>. */

import { torniumFetch } from "./api.js";
import { injectMemberSelector, injectStyles, updateMemberOptimums } from "./crime-page.js";
import { APP_ID, CACHE_ENABLED, DEBUG, GM_PREFIX, VERSION } from "./constants.js";
import { waitForElement } from "./dom.js";
import { log } from "./logging.js";
import { resolveToken, isAuthExpired, redirectURI } from "./oauth.js";
import { createSettingsButton, injectSettingsPage, injectSettingsStyles } from "./settings.js";

log(`Loading userscript v${VERSION}${DEBUG ? " with debug" : ""}${CACHE_ENABLED ? " with cache" : ""}...`);

const query = new URLSearchParams(document.location.search);

function executeCrimes() {
    createSettingsButton();
    injectStyles();

    torniumFetch("user", { ttl: 1000 * 60 * 60 })
        .then((identityData) => {
            return [identityData.factiontid, identityData.tid];
        })
        .then(([factionID, userID]) => {
            GM_setValue(`${GM_PREFIX}:userID`, userID);

            return Promise.all([
                torniumFetch(`faction/${factionID}/crime/member/${userID}/optimum`, { ttl: 60 }),
                userID,
                factionID,
                waitForElement(`#faction-crimes-root [class*="buttonsContainer__"]`),
            ]);
        })
        .then(([data, userID, factionID, memberSelectorContainer]) => {
            if (memberSelectorContainer == null) {
                log("Failed to load container .buttonsContainer for the memberSelector");
                throw new Error("Failed to find container for memberSelector");
            }

            injectMemberSelector(memberSelectorContainer, userID, factionID);
            updateMemberOptimums(data);
        });
}

if (window.location.pathname.startsWith(`/tornium/${APP_ID}/settings`)) {
    const errorContainer = document.getElementsByClassName("main-wrap")[0];
    const errorContainerTitle = document.getElementById("skip-to-content");

    if (errorContainer == undefined || errorContainerTitle == undefined) {
        log("Failed to load settings page: missing error container");
    } else {
        errorContainer.innerHTML = "";
        errorContainerTitle.innerText = "Tornium Crimes Settings";

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

    const localState = GM_getValue(`${GM_PREFIX}:state`);
    const localCodeVerifier = GM_getValue(`${GM_PREFIX}:codeVerifier`);

    if (callbackState === localState) {
        resolveToken(callbackCode, callbackState, localCodeVerifier);
        log("Succesfully authenticated the OAuth token");
        // NOTE: The redirect will occur inside the resolveToken callback
    } else {
        unsafeWindow.alert("Invalid security state. Try again.");
        log("Callback state: " + callbackState);
        log("Local state: " + localState);
        window.location.href = "https://www.torn.com";
    }
} else if (
    window.location.pathname.startsWith("/factions.php") &&
    query.get("step") == "your" &&
    window.location.hash == "#/tab=crimes" &&
    !isAuthExpired()
) {
    // TODO: Clean this up
    executeCrimes();

    window.addEventListener("hashchange", (event) => {
        const newURL = new URL(event.newURL);
        if (!newURL.pathname.startsWith("/factions.php")) {
            return;
        } else if (newURL.hash != "#/tab=crimes") {
            return;
        }

        const newQuery = new URLSearchParams(newURL.search);

        if (newQuery.get("step") != "your") {
            return;
        }

        executeCrimes();
    });
} else if (window.location.pathname.startsWith("/factions.php")) {
    // Fallback on the faction page to ensure the settings button is created regardless of:
    //  - the faction URI being malformed
    //  - the OAuth token being expired
    createSettingsButton();

    window.addEventListener("hashchange", (event) => {
        const newURL = new URL(event.newURL);
        if (!newURL.pathname.startsWith("/factions.php")) {
            return;
        } else if (newURL.hash != "#/tab=crimes") {
            return;
        }

        const newQuery = new URLSearchParams(newURL.search);

        if (newQuery.get("step") != "your") {
            return;
        }

        executeCrimes();
    });
}
