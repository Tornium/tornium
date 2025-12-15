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
import { Config } from "./config.js";
import { APP_ID, CACHE_ENABLED, DEBUG, VERSION } from "./constants.js";
import { waitForElement } from "./dom.js";
import { log } from "./logging.js";
import { resolveToken, isAuthExpired, redirectURI } from "./oauth.js";
import { injectAttackLoaderStats } from "./pages/attack-loader.js";
import { checkRankedWarToggleState } from "./pages/faction-rw.js";
import { createProfileContainer, updateProfileStatsSpan, updateProfileEstimateSpan } from "./pages/profile.js";
import { startSearchUserListObserver } from "./pages/search.js";
import { createSettingsButton, injectSettingsPage, injectSettingsStyles } from "./settings.js";
import { getUserEstimate, getUserStats } from "./stats.js";

log(`Loading userscript v${VERSION}${DEBUG ? " with debug" : ""}${CACHE_ENABLED ? " with cache" : ""}...`);

function isEnabledOn(pageID) {
    return Config.pages.some((page) => page == pageID);
}

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
        log("Succesfully authenticated the OAuth token");
        // NOTE: The redirect will occur inside the resolveToken callback
    } else {
        unsafeWindow.alert("Invalid security state. Try again.");
        log("Callback state: " + callbackState);
        log("Local state: " + localState);
        window.location.href = "https://www.torn.com";
    }
} else if (
    window.location.pathname.startsWith("/profiles.php") &&
    !isNaN(parseInt(query.get("XID"))) &&
    isEnabledOn("profile") &&
    !isAuthExpired()
) {
    const userID = parseInt(query.get("XID"));
    createSettingsButton();
    const [statsSpan, estimateSpan] = createProfileContainer();

    getUserStats(userID).then((statsData) => {
        updateProfileStatsSpan(statsData, statsSpan);
    });
    getUserEstimate(userID).then((estimateData) => {
        updateProfileEstimateSpan(estimateData, estimateSpan);
    });
} else if (window.location.pathname.startsWith("/profiles.php")) {
    // Fallback on the profile page to ensure the settings button is created regardless of:
    //  - the profile URI being malformed and not including a user ID
    //  - estimates not being enabled on the profile page
    //  - the OAuth token being expired
    createSettingsButton();
} else if (window.location.pathname.startsWith("/gym.php")) {
    // We're waiting for dexterity as we're assuming it's the last node to be injected into the DOM.
    waitForElement(`li[class^="dexterity_"]`).then((parent) => {
        const strengthNode = document.querySelector(`li[class^="strength_"] span[class^="propertyValue_"]`);
        const defenseNode = document.querySelector(`li[class^="defense_"] span[class^="propertyValue_"]`);
        const speedNode = document.querySelector(`li[class^="speed_"] span[class^="propertyValue_"]`);
        const dexterityNode = document.querySelector(`li[class^="dexterity_"] span[class^="propertyValue_"]`);

        const strength = parseInt(strengthNode.innerText.split(",").join(""));
        const defense = parseInt(defenseNode.innerText.split(",").join(""));
        const speed = parseInt(speedNode.innerText.split(",").join(""));
        const dexterity = parseInt(dexterityNode.innerText.split(",").join(""));

        // We're using a naive rounding instead of rounding to two decimal places as the difference in precision is insignificant
        Config.statScore = Math.round(
            Math.sqrt(strength) + Math.sqrt(defense) + Math.sqrt(speed) + Math.sqrt(dexterity),
        );
    });
} else if (window.location.pathname.startsWith("/factions.php")) {
    if (isEnabledOn("faction-rw")) {
        waitForElement(`div[class^="rankBox_"]`).then((rankedWarBox) => {
            rankedWarBox.addEventListener("click", checkRankedWarToggleState);
        });

        checkRankedWarToggleState();
    }
} else if (window.location.pathname == "/page.php" && query.get("sid") == "UserList" && isEnabledOn("search")) {
    startSearchUserListObserver();
} else if (window.location.pathname == "/loader.php" && query.get("sid") == "attack" && isEnabledOn("attack-loader")) {
    const userID = parseInt(query.get("user2ID"));

    if (!isNaN(userID) && userID != null) {
        injectAttackLoaderStats(userID);
    }
}
