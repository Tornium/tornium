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
import { APP_ID, DEBUG, VERSION } from "./constants.js";
import { log } from "./logging.js";
import { resolveToken, isAuthExpired, redirectURI } from "./oauth.js";
import { createProfileContainer } from "./pages/profile.js";
import { createSettingsButton, injectSettingsPage, injectSettingsStyles } from "./settings.js";
import { getUserStats } from "./stats.js";

log(`Loading userscript v${VERSION}${DEBUG ? " with debug" : ""}...`);

const query = new URLSearchParams(document.location.search);

if (window.location.pathname.startsWith(`/tornium/${APP_ID}/settings`)) {
    const errorContainer = document.getElementsByClassName("main-wrap")[0];
    const errorContainerTitle = document.getElementById("skip-to-content");

    if (errorContainer == undefined || errorContainerTitle == undefined) {
        log("Failed to load settings page: missing error container");
    } else {
        errorContainer.innerHTML = "";
        errorContainerTitle.innerText = "Tornium Estimate Settings";

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

    const localState = GM_getValue("tornium-estimate:state");
    const localCodeVerifier = GM_getValue("tornium-estimate:codeVerifier");
    if (callbackState === localState) {
        resolveToken(callbackCode, callbackState, localCodeVerifier);
    } else {
        unsafeWindow.alert("Invalid security state. Try again.");
        window.location.href = "https://www.torn.com";
    }
} else if (window.location.pathname.startsWith("/profiles.php") && isAuthExpired()) {
    createSettingsButton();
} else if (
    window.location.pathname.startsWith("/profiles.php") &&
    !isNaN(parseInt(query.get("XID"))) &&
    !isAuthExpired()
) {
    const userID = parseInt(query.get("XID"));
    createSettingsButton();

    const [statsPromise, estimatePromise] = getUserStats(userID);
    const [statsSpan, estimateSpan] = createProfileContainer();

    statsPromise.then((statsData) => {
        console.log(statsData);
    });
    estimatePromise.then((estimateData) => {
        console.log(estimateData);
    });
}
