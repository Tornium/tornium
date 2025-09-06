import { APP_ID, BASE_URL, VERSION } from "./constants.js";
import { log } from "./logging.js";
import { accessToken, authorizationURL, authStatus, isAuthExpired } from "./oauth.js";

function arrayToString(array) {
    return btoa(String.fromCharCode.apply(null, array)).replaceAll("=", "").replaceAll("+", "-").replaceAll("/", "_");
}

export function createSettingsButton() {
    if (!window.location.pathname.startsWith("/factions.php")) {
        // The settings link will only be loaded from the faction page
        return;
    }

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
    settingsIcon.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="17" height="18" viewBox="0 0 17 18"><title>tornium_retaliations_settings</title><g id="Layer_2" data-name="Layer 2"><g id="icons"><g opacity="0.35"><path d="M0,1A45.3,45.3,0,0,0,8.37,11.62l.13.14h0l2.39,2.41a19,19,0,0,1-2.16,1.46l1,1,2.48-2.49A13.08,13.08,0,0,1,16,18l1-1a11.76,11.76,0,0,1-3.82-3.77l2.48-2.5-1-1a12.92,12.92,0,0,1-1.42,2.2c-1.58-1.59-3.11-3.12-4.69-4.56l0,0A45.48,45.48,0,0,0,0,1ZM17,1A45,45,0,0,0,9,6.85l.82.78,2-2.06.48.48-2,2,.88.85A37.65,37.65,0,0,0,17,1ZM5.13,5.57l7.22,7.27-.48.48L4.65,6.05ZM2.37,9.68l-1,1,2.48,2.5A11.76,11.76,0,0,1,0,17l1,1a13.08,13.08,0,0,1,3.75-3.84l2.48,2.49,1-1a19,19,0,0,1-2.16-1.46L8,12.24l-.89-.93-2,2-.48-.48,2-2L5.78,9.9c-.66.64-1.32,1.3-2,2a12.92,12.92,0,0,1-1.42-2.2Z" fill="#fff"></path></g><path d="M0,0A45.3,45.3,0,0,0,8.37,10.62l.13.14h0l2.39,2.41a19,19,0,0,1-2.16,1.46l1,1,2.48-2.49A13.08,13.08,0,0,1,16,17l1-1a11.76,11.76,0,0,1-3.82-3.77l2.48-2.5-1-1a12.92,12.92,0,0,1-1.42,2.2C11.63,9.29,10.1,7.76,8.52,6.32l0,0A45.48,45.48,0,0,0,0,0ZM17,0A45,45,0,0,0,9,5.85l.82.78,2-2.06.48.48-2,2,.88.85A37.65,37.65,0,0,0,17,0ZM5.13,4.57l7.22,7.27-.48.48L4.65,5.05ZM2.37,8.68l-1,1,2.48,2.5A11.76,11.76,0,0,1,0,16l1,1a13.08,13.08,0,0,1,3.75-3.84l2.48,2.49,1-1a19,19,0,0,1-2.16-1.46L8,11.24l-.89-.93-2,2-.48-.48,2-2L5.78,8.9c-.66.64-1.32,1.3-2,2a12.92,12.92,0,0,1-1.42-2.2Z" fill="#777"></path></g></g></svg>`;
    settingsButton.append(settingsIcon);

    const settingsLabel = document.createElement("span");
    settingsLabel.innerText = "Retal Settings";
    settingsButton.append(settingsLabel);

    pageLinks.append(settingsButton);
}

export function injectSettingsPage(container) {
    container.classList.add("tornium-retaliations-settings");

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
    oauthScopes.append("faction:attacks");
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
    GM_setValue("tornium-retaliations:state", oauthState);
    GM_setValue("tornium-retaliations:codeVerifier", oauthCodeVerifier);

    if (isAuthExpired()) {
        oauthConnectButton.innerText = "Connect";
    } else {
        oauthConnectButton.innerText = "Reconnect";

        const oauthDisconnectButton = document.createElement("button");
        oauthDisconnectButton.classList.add("torn-btn");
        oauthDisconnectButton.innerText = "Disconnect";
        // TODO: Add event listener callback
        // oauthDisconnectButton.addEventListener("click", null);
        oauthSection.append(oauthDisconnectButton);
    }

    container.append(oauthSection);

    container.append(document.createElement("hr"));

    const configSection = document.createElement("fieldset");
    const configLegend = document.createElement("legend");
    configLegend.innerText = "Configuration";
    configSection.append(configLegend);

    // TODO: Add update interval
    // TODO: Add sort order
    // TODO: Add filter to determine the pages it will run on

    container.append(configSection);

    const infoContainer = document.createElement("fieldset");
    const infoLegend = document.createElement("legend");
    infoLegend.innerText = "About and Privacy";
    infoContainer.append(infoLegend);

    container.append(document.createElement("hr"));

    const infoScriptContainer = document.createElement("div");
    const infoScriptVersion = document.createElement("p");
    infoScriptVersion.innerHTML = `<strong>Version: </strong> v${VERSION}`;
    infoScriptContainer.append(infoScriptVersion);
    const infoScriptLink = document.createElement("p");
    infoScriptLink.innerHTML = `<strong>Link: </strong> <a href="https://github.com/Tornium/tornium/blob/master/userscripts/tornium-retaliations.user.js">GitHub</a>`;
    infoScriptContainer.append(infoScriptLink);
    const infoScriptDocs = document.createElement("p");
    infoScriptDocs.innerHTml = `<strong>Docs: </strong> Not yet created`;
    infoScriptContainer.append(infoScriptDocs);
    infoContainer.append(infoScriptContainer);

    container.append(infoContainer);
}

export function injectSettingsStyles() {
    GM_addStyle(`
        .tornium-retaliations-settings {
            margin-top: 10px;
        }

        .tornium-retaliations-settings hr {
            border: none;
            border-top: 1px solid #444;
            margin-top: 20px !important;
            margin-bottom: 20px !important;
        }

        .tornium-retaliations-settings fieldset {
            border: 1px solid #555;
            border-radius: 6px;
            padding: 16px;
            margin-bottom: 20px;
            background: rgba(0, 0, 0, 0.25);
        }

        .tornium-retaliations-settings legend {
            font-size: 1.2rem;
            font-weight: bold;
            padding: 0 6px;
            color: #fff;
        }

        .tornium-retaliations-settings .torn-btn {
            display: inline-block;
            margin: 8px 6px 0 0;
        }
    `);
}
