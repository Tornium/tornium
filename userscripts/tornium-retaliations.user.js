// ==UserScript==
// @name         Tornium Retalations
// @version      0.1.0-dev
// @copyright    GPLv3
// @author       tiksan [2383326]
// @match        https://tornium.com/oauth/80698282ed024680b0e3a9439bb764aab4d4d3b27ca087af/callback*
// @match        https://www.torn.com/tornium/80698282ed024680b0e3a9439bb764aab4d4d3b27ca087af/oauth/callback*
// @match        https://www.torn.com/tornium/80698282ed024680b0e3a9439bb764aab4d4d3b27ca087af/settings
// @match        https://www.torn.com/profiles.php*
// @match        https://www.torn.com/loader.php?sid=attack*
// @match        https://www.torn.com/factions.php*
// @grant        GM_xmlhttpRequest
// @grant        GM_getValue
// @grant        GM_setValue
// @grant        GM_deleteValue
// @grant        GM_addStyle
// @connect      tornium.com
// @downloadURL  https://github.com/Tornium/tornium/raw/refs/heads/master/userscripts/tornium-retaliations.user.js
// @updateURL    https://github.com/Tornium/tornium/raw/refs/heads/master/userscripts/tornium-retaliations.user.js
// @supportURL   https://discord.gg/pPcqTRTRyF
// ==/UserScript==

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
(() => {
  // constants.js
  var DEBUG = false;
  var BASE_URL = DEBUG ? "http://127.0.0.1:5000" : "https://tornium.com";
  var VERSION = "0.1.0-dev";
  var APP_ID = "80698282ed024680b0e3a9439bb764aab4d4d3b27ca087af";
  var APP_SCOPE = "identity faction:attacks";
  GM_setValue("tornium-retaliations:test", "1");
  var clientLocalGM = localStorage.getItem("tornium-retaliations:test") === "1";

  // oauth.js
  var accessToken = GM_getValue("tornium-retaliations:access-token", null);
  var accessTokenExpiration = GM_getValue("tornium-retaliations:access-token-expires", 0);
  var redirectURI = clientLocalGM ? `https://www.torn.com/tornium/${APP_ID}/oauth/callback` : `${BASE_URL}/oauth/${APP_ID}/callback`;
  console.log("Token: " + accessToken);
  console.log("Token Expiration: " + accessTokenExpiration);
  function isAuthExpired() {
    if (accessToken == null || accessTokenExpiration == 0) {
      return true;
    } else if (Math.floor(Date.now() / 1e3) >= accessTokenExpiration) {
      return true;
    }
    return false;
  }
  function authStatus() {
    if (accessToken == null) {
      return "Disconnected";
    } else if (isAuthExpired()) {
      return "Expired";
    }
    return "Connected";
  }
  function authorizationURL(oauthState, codeChallenge) {
    return `${BASE_URL}/oauth/authorize?response_type=code&client_id=${APP_ID}&state=${oauthState}&scope=${APP_SCOPE}&code_challenge_method=S256&code_challenge=${codeChallenge}&redirect_uri=${redirectURI}`;
  }
  function resolveToken(code, state, codeVerifier) {
    console.log("Code: " + code);
    const tokenData = new URLSearchParams();
    tokenData.set("code", code);
    tokenData.set("grant_type", "authorization_code");
    tokenData.set("scope", APP_SCOPE);
    tokenData.set("client_id", APP_ID);
    tokenData.set("code_verifier", codeVerifier);
    tokenData.set("redirect_uri", redirectURI);
    GM_xmlhttpRequest({
      method: "POST",
      url: `${BASE_URL}/oauth/token`,
      headers: {
        "Content-Type": "application/x-www-form-urlencoded"
      },
      data: tokenData.toString(),
      responseType: "json",
      onload: resolveTokenCallback
    });
  }
  function resolveTokenCallback(response) {
    let responseJSON = response.response;
    if (response.responseType === void 0) {
      responseJSON = JSON.parse(response.responseText);
      response.responseType = "json";
    }
    console.log(responseJSON);
    const accessToken2 = responseJSON.access_token;
    const accessTokenExpiration2 = Math.floor(Date.now() / 1e3) + responseJSON.expires_in;
    GM_setValue("tornium-retaliations:access-token", accessToken2);
    GM_setValue("tornium-retaliations:access-token-expires", accessTokenExpiration2);
    window.location.href = "https://torn.com";
    return;
  }

  // api.js
  function tornium_fetch(endpoint, options = { method: "GET" }) {
    return new Promise(async (resolve, reject) => {
      return GM_xmlhttpRequest({
        method: options.method,
        url: `${BASE_URL}/api/v1/${endpoint}`,
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`
        },
        responseType: "json",
        onload: async (response) => {
          let responseJSON = response.response;
          console.log(responseJSON);
          if (response.responseType === void 0) {
            responseJSON = JSON.parse(response.responseText);
            response.responseType = "json";
          }
          if (responseJSON.error !== void 0) {
            GM_deleteValue("tornium-retaliations:access-token");
            GM_deleteValue("tornium-retaliations:access-token-expires");
            $("#tornium-estimation").text(
              `[${responseJSON.error}] OAuth Error - ${responseJSON.error_description}`
            );
            reject();
            return;
          }
          resolve(responseJSON);
          return;
        },
        onerror: (error) => {
          reject(error);
          return;
        }
      });
    });
  }

  // logging.js
  function log(string) {
    if (!DEBUG) {
      return;
    }
    console.log("[Tornium Retaliations] " + window.location.pathname + " - " + string);
  }

  // settings.js
  function arrayToString(array) {
    return btoa(String.fromCharCode.apply(null, array)).replaceAll("=", "").replaceAll("+", "-").replaceAll("/", "_");
  }
  function createSettingsButton() {
    if (!window.location.pathname.startsWith("/factions.php")) {
      return;
    }
    const pageLinks = document.getElementById("top-page-links-list");
    if (pageLinks == void 0) {
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
  function injectSettingsPage(container) {
    container.classList.add("tornium-retaliations-settings");
    const descriptionSection = document.createElement("p");
    descriptionSection.innerText = "Configure authentication and settings for the script. Also view info about the script.";
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
    oauthScopes.append("identity faction:attacks");
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
      oauthDisconnectButton.addEventListener("click", deleteOAuthToken);
      oauthSection.append(oauthDisconnectButton);
    }
    container.append(oauthSection);
    container.append(document.createElement("hr"));
    const configSection = document.createElement("fieldset");
    const configLegend = document.createElement("legend");
    configLegend.innerText = "Configuration";
    configSection.append(configLegend);
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
  function injectSettingsStyles() {
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
  function deleteOAuthToken() {
    GM_deleteValue("tornium-retaliations:access-token");
    GM_deleteValue("tornium-retaliations:access-token-expires");
    window.location.reload();
  }

  // entrypoint.js
  log(`Loading userscript v${VERSION}${DEBUG ? " with debug" : ""}...`);
  if (window.location.pathname.startsWith(`/tornium/${APP_ID}/settings`)) {
    const errorContainer = document.getElementsByClassName("main-wrap")[0];
    const errorContainerTitle = document.getElementById("skip-to-content");
    if (errorContainer == void 0 || errorContainerTitle == void 0) {
      log("Failed to load settings page: missing error container");
    } else {
      errorContainer.innerHTML = "";
      errorContainerTitle.innerText = "Tornium Retaliation Settings";
      injectSettingsStyles();
      injectSettingsPage(errorContainer);
    }
  } else if (window.location.pathname == new URL(redirectURI).pathname && window.location.host == new URL(redirectURI).host) {
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
  } else if (window.location.pathname.startsWith("/factions.php") && new URLSearchParams(window.location.search).get("step") == "your") {
    createSettingsButton();
    tornium_fetch("user").then((identityData) => {
      const factionID = identityData.factiontid;
    });
  }
})();
