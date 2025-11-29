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

import { PAGE_OPTIONS, Config } from "./config.js";
import { APP_ID, BASE_URL, VERSION } from "./constants.js";
import { log } from "./logging.js";
import { accessToken, authorizationURL, authStatus, isAuthExpired } from "./oauth.js";

function arrayToString(array) {
    return btoa(String.fromCharCode.apply(null, array)).replaceAll("=", "").replaceAll("+", "-").replaceAll("/", "_");
}

export function createSettingsButton() {
    const pageLinks = document.getElementById("top-page-links-list");

    if (pageLinks == undefined) {
        log("Missing page links element");
        return;
    }

    const settingsButton = document.createElement("a");
    settingsButton.classList.add("t-clear", "h", "c-pointer", "m-icon", "line-h24", "right", "last");
    settingsButton.setAttribute("href", `/tornium/${APP_ID}/settings`);

    const settingsIcon = document.createElement("span");
    settingsIcon.classList.add("icon-wrap", "svg-icon-wrap", "link-icon-svg");
    settingsIcon.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="17" height="18" viewBox="0 0 17 18"><title>tornium_estimate_settings</title><g id="Layer_2" data-name="Layer 2"><g id="icons"><g opacity="0.35"><path d="M0,1A45.3,45.3,0,0,0,8.37,11.62l.13.14h0l2.39,2.41a19,19,0,0,1-2.16,1.46l1,1,2.48-2.49A13.08,13.08,0,0,1,16,18l1-1a11.76,11.76,0,0,1-3.82-3.77l2.48-2.5-1-1a12.92,12.92,0,0,1-1.42,2.2c-1.58-1.59-3.11-3.12-4.69-4.56l0,0A45.48,45.48,0,0,0,0,1ZM17,1A45,45,0,0,0,9,6.85l.82.78,2-2.06.48.48-2,2,.88.85A37.65,37.65,0,0,0,17,1ZM5.13,5.57l7.22,7.27-.48.48L4.65,6.05ZM2.37,9.68l-1,1,2.48,2.5A11.76,11.76,0,0,1,0,17l1,1a13.08,13.08,0,0,1,3.75-3.84l2.48,2.49,1-1a19,19,0,0,1-2.16-1.46L8,12.24l-.89-.93-2,2-.48-.48,2-2L5.78,9.9c-.66.64-1.32,1.3-2,2a12.92,12.92,0,0,1-1.42-2.2Z" fill="#fff"></path></g><path d="M0,0A45.3,45.3,0,0,0,8.37,10.62l.13.14h0l2.39,2.41a19,19,0,0,1-2.16,1.46l1,1,2.48-2.49A13.08,13.08,0,0,1,16,17l1-1a11.76,11.76,0,0,1-3.82-3.77l2.48-2.5-1-1a12.92,12.92,0,0,1-1.42,2.2C11.63,9.29,10.1,7.76,8.52,6.32l0,0A45.48,45.48,0,0,0,0,0ZM17,0A45,45,0,0,0,9,5.85l.82.78,2-2.06.48.48-2,2,.88.85A37.65,37.65,0,0,0,17,0ZM5.13,4.57l7.22,7.27-.48.48L4.65,5.05ZM2.37,8.68l-1,1,2.48,2.5A11.76,11.76,0,0,1,0,16l1,1a13.08,13.08,0,0,1,3.75-3.84l2.48,2.49,1-1a19,19,0,0,1-2.16-1.46L8,11.24l-.89-.93-2,2-.48-.48,2-2L5.78,8.9c-.66.64-1.32,1.3-2,2a12.92,12.92,0,0,1-1.42-2.2Z" fill="#777"></path></g></g></svg>`;
    settingsButton.append(settingsIcon);

    const settingsLabel = document.createElement("span");
    settingsLabel.innerText = "Estimate Settings";
    settingsButton.append(settingsLabel);

    pageLinks.append(settingsButton);
}

export function injectSettingsPage(container) {
    container.classList.add("tornium-estimate-settings");

    const descriptionSection = document.createElement("p");
    descriptionSection.innerText =
        "Configure authentication and settings for the script. Also view info about the script.";
    container.append(descriptionSection);

    container.append(document.createElement("hr"));

    const oauthSection = document.createElement("fieldset");
    const oauthLegend = document.createElement("legend");
    oauthLegend.innerText = "Authentication";
    oauthSection.append(oauthLegend);

    const oauthStatus = document.createElement("span");
    const oauthStatusLabel = document.createElement("strong");
    oauthStatusLabel.innerText = "Status: ";
    oauthStatus.append(oauthStatusLabel);
    oauthStatus.append(authStatus());
    oauthSection.append(oauthStatus);

    const oauthScopes = document.createElement("p");
    const oauthScopesLabel = document.createElement("strong");
    oauthScopesLabel.innerText = "Scope(s): ";
    oauthScopes.append(oauthScopesLabel);
    oauthScopes.append("identity api_key:usage");
    oauthSection.append(oauthScopes);

    const oauthConnectButton = document.createElement("a");
    oauthConnectButton.classList.add("torn-btn");
    oauthSection.append(oauthConnectButton);

    const oauthState = arrayToString(window.crypto.getRandomValues(new Uint8Array(24)));
    const oauthCodeVerifier = arrayToString(window.crypto.getRandomValues(new Uint8Array(48)));
    window.crypto.subtle.digest("SHA-256", new TextEncoder().encode(oauthCodeVerifier)).then((buffer) => {
        const oauthCodeChallenge = arrayToString(new Uint8Array(buffer));
        oauthConnectButton.setAttribute("href", authorizationURL(oauthState, oauthCodeChallenge));
    });
    GM_setValue("tornium-estimate:state", oauthState);
    GM_setValue("tornium-estimate:codeVerifier", oauthCodeVerifier);

    if (isAuthExpired()) {
        oauthConnectButton.innerText = "Connect";
    } else {
        oauthConnectButton.innerText = "Reconnect";

        const oauthDisconnectButton = document.createElement("button");
        oauthDisconnectButton.classList.add("torn-btn");
        oauthDisconnectButton.innerText = "Disconnect";
        oauthDisconnectButton.addEventListener("click", deleteOAuthToken);
        oauthSection.append(oauthDisconnectButton);
    }

    container.append(oauthSection);

    container.append(document.createElement("hr"));

    // === Config
    const configSection = document.createElement("fieldset");
    const configLegend = document.createElement("legend");
    configLegend.innerText = "Configuration";
    configSection.append(configLegend);

    // === Config: Show exact stat instead of showing a shortened form of the stat (3.2B)
    const configExactStatLabel = document.createElement("label");
    configExactStatLabel.for = "tornium-estimate-settings-exact-stat";
    configExactStatLabel.innerText = "Show exact values instead of shortened: ";
    configExactStatLabel.style.display = "inline";
    configSection.append(configExactStatLabel);

    const configExactStatCheckbox = document.createElement("input");
    configExactStatCheckbox.id = "tornium-estimate-settings-exact-stat";
    configExactStatCheckbox.type = "checkbox";
    configExactStatCheckbox.checked = Config.exactStat;
    configExactStatCheckbox.addEventListener("change", (event) => {
        Config.exactStat = configExactStatCheckbox.checked;
    });
    configSection.append(configExactStatCheckbox);

    // === Config: Select the pages for the stat estimates to be shown on
    const configPagesLabel = document.createElement("label");
    configPagesLabel.for = "tornium-estimate-settings-pages";
    configPagesLabel.innerText = "Enable stats/estimated stats on the following pages: ";
    configPagesLabel.style.display = "block";
    configPagesLabel.style.marginTop = "10px";
    configSection.append(configPagesLabel);

    const configPagesListGroup = document.createElement("div");
    configPagesListGroup.style.borderTop = "1px solid #444";
    configPagesListGroup.style.borderBottom = "1px solid #444";
    configPagesListGroup.style.marginTop = "5px";
    configSection.append(configPagesListGroup);

    PAGE_OPTIONS.forEach((page) => {
        const row = document.createElement("label");
        row.style.display = "flex";
        row.style.alignItems = "center";
        row.style.padding = "8px 10px";
        row.style.borderBottom = "1px solid #333";
        row.style.cursor = "pointer";
        row.style.userSelect = "none";

        row.addEventListener("mouseover", () => (row.style.background = "rgba(255,255,255,0.05)"));
        row.addEventListener("mouseout", () => (row.style.background = "transparent"));

        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.checked = Config.pages.includes(page.id);
        checkbox.style.marginRight = "10px";

        checkbox.addEventListener("change", () => {
            let pages = Config.pages;

            if (checkbox.checked && !pages.includes(page.id)) {
                pages.push(page.id);
            } else if (!checkbox.checked) {
                pages = pages.filter((x) => x !== page.id);
            }

            Config.pages = pages;
        });

        const text = document.createElement("span");
        text.innerText = page.label;

        row.append(checkbox);
        row.append(text);
        configPagesListGroup.append(row);
    });

    container.append(configSection);

    // === Info
    const infoContainer = document.createElement("fieldset");
    const infoLegend = document.createElement("legend");
    infoLegend.innerText = "About and Privacy";
    infoContainer.append(infoLegend);

    container.append(document.createElement("hr"));

    // == Info: Links such as ToS
    const infoScriptContainer = document.createElement("div");
    const infoScriptVersion = document.createElement("p");
    infoScriptVersion.innerHTML = `<strong>Version: </strong> v${VERSION}`;
    infoScriptContainer.append(infoScriptVersion);
    const infoScriptLink = document.createElement("p");
    infoScriptLink.innerHTML = `<strong>Link: </strong> <a href="https://github.com/Tornium/tornium/blob/master/userscripts/tornium-estimate.user.js">GitHub</a>`;
    infoScriptContainer.append(infoScriptLink);
    const infoScriptDocs = document.createElement("p");
    infoScriptDocs.innerHTML = `<strong>Documentation: </strong> <a href="https://docs.tornium.com/en/latest/reference/tornium-estimate.html">docs.tornium.com</a>`;
    infoScriptContainer.append(infoScriptDocs);
    const infoScriptTerms = document.createElement("p");
    infoScriptTerms.innerHTML = `<strong>Terms of Service: </strong> This userscript falls under Tornium's <a href="https://tornium.com/terms">Terms of Service</a> and <a href="https://tornium.com/privacy">Privacy Policy</a>.`;
    infoScriptContainer.append(infoScriptTerms);
    infoContainer.append(infoScriptContainer);

    container.append(infoContainer);
}

export function injectSettingsStyles() {
    GM_addStyle(`
.tornium-estimate-settings {
margin-top: 10px;
}

.tornium-estimate-settings hr {
border: none;
border-top: 1px solid #444;
margin-top: 20px !important;
margin-bottom: 20px !important;
}

.tornium-estimate-settings fieldset {
border: 1px solid #555;
border-radius: 6px;
padding: 16px;
margin-bottom: 20px;
background: rgba(0, 0, 0, 0.25);
}

.tornium-estimate-settings legend {
font-size: 1.2rem;
font-weight: bold;
padding: 0 6px;
color: #fff;
}

.tornium-estimate-settings .torn-btn {
display: inline-block;
margin: 8px 6px 0 0;
}
`);
}

function deleteOAuthToken() {
    GM_deleteValue("tornium-estimate:access-token");
    GM_deleteValue("tornium-estimate:access-token-expires");
    window.location.reload();
}
