// ==UserScript==
// @name         Tornium Crimes
// @namespace    https://tornium.com
// @version      0.1.0
// @copyright    GPLv3
// @author       tiksan [2383326]
// @match        https://www.torn.com/factions.php*
// @match        https://tornium.com/oauth/97884c32bb18b41224f482390d9f712268e1240082cdc6b9/callback*
// @match        http://127.0.0.1:5000/oauth/97884c32bb18b41224f482390d9f712268e1240082cdc6b9/callback*
// @match        https://www.torn.com/tornium/97884c32bb18b41224f482390d9f712268e1240082cdc6b9/oauth/callback*
// @match        https://www.torn.com/tornium/97884c32bb18b41224f482390d9f712268e1240082cdc6b9/settings
// @grant        GM_xmlhttpRequest
// @grant        GM_getValue
// @grant        GM_setValue
// @grant        GM_deleteValue
// @grant        GM_addStyle
// @connect      tornium.com
// @downloadURL  https://github.com/Tornium/tornium/raw/refs/heads/master/userscripts/tornium-crimes.user.js
// @updateURL    https://github.com/Tornium/tornium/raw/refs/heads/master/userscripts/tornium-crimes.user.js
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
  var DEBUG = true;
  var BASE_URL = "https://tornium.com";
  var ENABLE_LOGGING = true;
  var VERSION = "0.1.0";
  var APP_ID = "97884c32bb18b41224f482390d9f712268e1240082cdc6b9";
  var APP_SCOPE = "identity faction:crimes";
  var CACHE_ENABLED = false;
  var GM_PREFIX = "tornium-crimes";
  var CACHE_NAME = `${GM_PREFIX}-cache`;
  GM_setValue(`${GM_PREFIX}:test`, "1");
  var localGMValue = localStorage.getItem(`${GM_PREFIX}:test`);
  var clientLocalGM = localGMValue === "1" || localGMValue === `GMV2_"1"`;
  var clientMobile = (() => {
    let check = false;
    (function(a) {
      if (/(android|bb\d+|meego).+mobile|avantgo|bada\/|blackberry|blazer|compal|elaine|fennec|hiptop|iemobile|ip(hone|od)|iris|kindle|lge |maemo|midp|mmp|mobile.+firefox|netfront|opera m(ob|in)i|palm( os)?|phone|p(ixi|re)\/|plucker|pocket|psp|series(4|6)0|symbian|treo|up\.(browser|link)|vodafone|wap|windows ce|xda|xiino/i.test(a) || /1207|6310|6590|3gso|4thp|50[1-6]i|770s|802s|a wa|abac|ac(er|oo|s\-)|ai(ko|rn)|al(av|ca|co)|amoi|an(ex|ny|yw)|aptu|ar(ch|go)|as(te|us)|attw|au(di|\-m|r |s )|avan|be(ck|ll|nq)|bi(lb|rd)|bl(ac|az)|br(e|v)w|bumb|bw\-(n|u)|c55\/|capi|ccwa|cdm\-|cell|chtm|cldc|cmd\-|co(mp|nd)|craw|da(it|ll|ng)|dbte|dc\-s|devi|dica|dmob|do(c|p)o|ds(12|\-d)|el(49|ai)|em(l2|ul)|er(ic|k0)|esl8|ez([4-7]0|os|wa|ze)|fetc|fly(\-|_)|g1 u|g560|gene|gf\-5|g\-mo|go(\.w|od)|gr(ad|un)|haie|hcit|hd\-(m|p|t)|hei\-|hi(pt|ta)|hp( i|ip)|hs\-c|ht(c(\-| |_|a|g|p|s|t)|tp)|hu(aw|tc)|i\-(20|go|ma)|i230|iac( |\-|\/)|ibro|idea|ig01|ikom|im1k|inno|ipaq|iris|ja(t|v)a|jbro|jemu|jigs|kddi|keji|kgt( |\/)|klon|kpt |kwc\-|kyo(c|k)|le(no|xi)|lg( g|\/(k|l|u)|50|54|\-[a-w])|libw|lynx|m1\-w|m3ga|m50\/|ma(te|ui|xo)|mc(01|21|ca)|m\-cr|me(rc|ri)|mi(o8|oa|ts)|mmef|mo(01|02|bi|de|do|t(\-| |o|v)|zz)|mt(50|p1|v )|mwbp|mywa|n10[0-2]|n20[2-3]|n30(0|2)|n50(0|2|5)|n7(0(0|1)|10)|ne((c|m)\-|on|tf|wf|wg|wt)|nok(6|i)|nzph|o2im|op(ti|wv)|oran|owg1|p800|pan(a|d|t)|pdxg|pg(13|\-([1-8]|c))|phil|pire|pl(ay|uc)|pn\-2|po(ck|rt|se)|prox|psio|pt\-g|qa\-a|qc(07|12|21|32|60|\-[2-7]|i\-)|qtek|r380|r600|raks|rim9|ro(ve|zo)|s55\/|sa(ge|ma|mm|ms|ny|va)|sc(01|h\-|oo|p\-)|sdk\/|se(c(\-|0|1)|47|mc|nd|ri)|sgh\-|shar|sie(\-|m)|sk\-0|sl(45|id)|sm(al|ar|b3|it|t5)|so(ft|ny)|sp(01|h\-|v\-|v )|sy(01|mb)|t2(18|50)|t6(00|10|18)|ta(gt|lk)|tcl\-|tdg\-|tel(i|m)|tim\-|t\-mo|to(pl|sh)|ts(70|m\-|m3|m5)|tx\-9|up(\.b|g1|si)|utst|v400|v750|veri|vi(rg|te)|vk(40|5[0-3]|\-v)|vm40|voda|vulc|vx(52|53|60|61|70|80|81|83|85|98)|w3c(\-| )|webc|whit|wi(g |nc|nw)|wmlb|wonu|x700|yas\-|your|zeto|zte\-/i.test(a.substr(0, 4))) check = true;
    })(navigator.userAgent || navigator.vendor || window.opera);
    return check;
  })();

  // cache.js
  var CACHE_EXPIRATION = 1e3 * 60 * 60 * 24;
  async function getCache(url) {
    if (!CACHE_ENABLED) {
      return null;
    }
    const cache = await caches.open(CACHE_NAME);
    const cachedResponse = await cache.match(url);
    if (cachedResponse) {
      const expirationTime = new Date(parseInt(cachedResponse.headers.get("cache-expiry")));
      if (Date.now() < expirationTime) {
        return await cachedResponse.json();
      }
      await cache.delete(url);
    }
    return null;
  }
  async function putCache(url, response, ttl = CACHE_EXPIRATION) {
    const headers = parseHeaders(response.responseHeaders);
    headers["cache-expiry"] = String(Date.now() + ttl);
    const cache = await caches.open(CACHE_NAME);
    await cache.put(url, new Response(response.responseText, { headers }));
  }
  function parseHeaders(headerString) {
    let headers = {};
    headerString.split("\r\n").forEach((line) => {
      const [key, value] = line.split(": ").map((item) => item.trim());
      if (key && value) {
        headers[key] = value;
      }
    });
    return headers;
  }

  // oauth.js
  var accessToken = GM_getValue(`${GM_PREFIX}:access-token`, null);
  var accessTokenExpiration = GM_getValue(`${GM_PREFIX}:access-token-expires`, 0);
  var redirectURI = clientLocalGM ? `https://www.torn.com/tornium/${APP_ID}/oauth/callback` : `${BASE_URL}/oauth/${APP_ID}/callback`;
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
    const accessToken2 = responseJSON.access_token;
    const accessTokenExpiration2 = Math.floor(Date.now() / 1e3) + responseJSON.expires_in;
    GM_setValue(`${GM_PREFIX}:access-token`, accessToken2);
    GM_setValue(`${GM_PREFIX}:access-token-expires`, accessTokenExpiration2);
    window.location.href = "https://torn.com";
    return;
  }

  // api.js
  function torniumFetch(endpoint, options = { method: "GET", ttl: CACHE_EXPIRATION }) {
    return new Promise(async (resolve, reject) => {
      const cachedResponse = await getCache(endpoint);
      if (cachedResponse != null && cachedResponse != void 0) {
        resolve(cachedResponse);
        return cachedResponse;
      }
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
          if (response.responseType === void 0) {
            try {
              responseJSON = JSON.parse(response.responseText);
              response.responseType = "json";
            } catch (err) {
              console.log(response.responseText);
              console.log(err);
              reject(err);
              return;
            }
          }
          if (responseJSON.error !== void 0) {
            GM_deleteValue(`${GM_PREFIX}:access-token`);
            GM_deleteValue(`${GM_PREFIX}:access-token-expires`);
            resolve(responseJSON);
            return responseJSON;
          }
          if (!("code" in responseJSON)) {
            putCache(endpoint, response, options.ttl);
          }
          resolve(responseJSON);
          return responseJSON;
        },
        onerror: (error) => {
          reject(error);
          return;
        }
      });
    });
  }

  // dom.js
  async function waitForElement(querySelector, timeout) {
    const existingElement = document.querySelector(querySelector);
    if (existingElement) return existingElement;
    return new Promise((resolve) => {
      let timer;
      const observer = new MutationObserver(() => {
        const element = document.querySelector(querySelector);
        if (element) {
          cleanup();
          resolve(element);
        }
      });
      observer.observe(document.body, {
        childList: true,
        subtree: true
      });
      if (timeout) {
        timer = setTimeout(() => {
          cleanup();
          resolve(null);
        }, timeout);
      }
      function cleanup() {
        observer.disconnect();
        if (timer) clearTimeout(timer);
      }
    });
  }

  // logging.js
  function log(string) {
    if (ENABLE_LOGGING || DEBUG) {
      console.log(`[${GM_PREFIX}] ${window.location.pathname} - ${string}`);
    }
  }

  // crime-page.js
  function injectMemberSelector(container, userID, factionID) {
    if (container == null) {
      return;
    }
    const wrapper = document.createElement("div");
    container.after(wrapper);
    const seperator = document.createElement("hr");
    seperator.classList.add("page-head-delimiter", "m-top10", "m-bottom10");
    wrapper.append(seperator);
    torniumFetch(`faction/${factionID}/members`, {}).then((memberData) => {
      const label = document.createElement("label");
      label.setAttribute("for", "tornium-crimes-optimum-member");
      label.textContent = "Faction Member (Optimum OC): ";
      wrapper.append(label);
      const selector = document.createElement("select");
      selector.setAttribute("name", "tornium-crimes-optimum-member");
      wrapper.append(selector);
      for (const member of memberData) {
        const option = document.createElement("option");
        option.setAttribute("value", member.ID);
        option.textContent = member.name;
        selector.append(option);
      }
      selector.value = userID;
      selector.addEventListener("change", onSelectedMemberChange);
    });
  }
  function updateMemberOptimums(optimumData) {
    console.log(optimumData);
    Promise.any([
      waitForElement(".tt-oc2-list"),
      waitForElement(`#faction-crimes-root hr.page-head-delimiter + div:has(> div[class^="wrapper___"][data-oc-id])`)
    ]).then((root) => {
      if (!root.classList.contains("tt-oc2-list")) {
        root.classList.add("tt-oc2-list");
      }
      const crimeElements = root.querySelectorAll(`[class*="wrapper___"][data-oc-id]`);
      for (const crimeElement of crimeElements) {
        const crimeID = parseInt(crimeElement.getAttribute("data-oc-id"));
        const slotElements = crimeElement.querySelectorAll(
          `[class*="wrapper___"]:has(> button[class*="slotHeader___"])`
        );
        if (crimeID == null || slotElements.length === 0) {
          continue;
        }
        for (const slotElement of slotElements) {
          const titleElement = slotElement.querySelector(`span[class*="title___"]`);
          const badgeContainer = slotElement.querySelector(`[class*="badgeContainer___"]`);
          badgeContainer.classList.add("tornium-crimes-slot-badge-container");
          if (badgeContainer == null || titleElement == null) {
            continue;
          }
          const slotData = optimumData.find((optimumSlotData) => {
            return optimumSlotData.oc_id == crimeID && `${optimumSlotData.oc_position} #${optimumSlotData.oc_position_index}` == titleElement.textContent || optimumSlotData.oc_position == titleElement.textContent;
          });
          if (slotData == null) {
            continue;
          }
          const slotInfo = document.createElement("div");
          slotInfo.classList.add("tornium-crimes-slot-info");
          slotInfo.textContent = `\u0394EV: ${(slotData.team_expected_value_change * 100).toFixed(2)}%; \u0394EV': ${(slotData.user_expected_value_change * 100).toFixed(2)}%; \u0394P: ${(slotData.team_probability_change * 100).toFixed(2)}%`;
          badgeContainer.prepend(slotInfo);
        }
      }
    });
  }
  function onSelectedMemberChange(event) {
    torniumFetch("user", { ttl: 1e3 * 60 * 60 }).then((identityData) => {
      return identityData.factiontid;
    }).then((factionID) => {
      return torniumFetch(`faction/${factionID}/crime/member/${event.target.value}/optimum`, { ttl: 60 });
    }).then((optimumData) => {
      return updateMemberOptimums(optimumData);
    });
  }
  function injectStyles() {
    GM_addStyle(".tornium-crimes-slot-info {padding-top: 0.5em; padding-bottom: 0.5em; margin: 0.25em;}");
    GM_addStyle(".tornium-crimes-slot-badge-container {flex-wrap: wrap; padding-bottom: 0.25em;}");
    GM_addStyle(
      `div[class*="slotBody___"] {height: inherit; height: stretch; height: -webkit-fill-available; height: 100%; min-height: 32px;}`
    );
  }

  // settings.js
  function arrayToString(array) {
    return btoa(String.fromCharCode.apply(null, array)).replaceAll("=", "").replaceAll("+", "-").replaceAll("/", "_");
  }
  function createSettingsButton() {
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
    settingsIcon.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="17" height="18" viewBox="0 0 17 18"><title>tornium_crimes_settings</title><g id="Layer_2" data-name="Layer 2"><g id="icons"><g opacity="0.35"><path d="M0,1A45.3,45.3,0,0,0,8.37,11.62l.13.14h0l2.39,2.41a19,19,0,0,1-2.16,1.46l1,1,2.48-2.49A13.08,13.08,0,0,1,16,18l1-1a11.76,11.76,0,0,1-3.82-3.77l2.48-2.5-1-1a12.92,12.92,0,0,1-1.42,2.2c-1.58-1.59-3.11-3.12-4.69-4.56l0,0A45.48,45.48,0,0,0,0,1ZM17,1A45,45,0,0,0,9,6.85l.82.78,2-2.06.48.48-2,2,.88.85A37.65,37.65,0,0,0,17,1ZM5.13,5.57l7.22,7.27-.48.48L4.65,6.05ZM2.37,9.68l-1,1,2.48,2.5A11.76,11.76,0,0,1,0,17l1,1a13.08,13.08,0,0,1,3.75-3.84l2.48,2.49,1-1a19,19,0,0,1-2.16-1.46L8,12.24l-.89-.93-2,2-.48-.48,2-2L5.78,9.9c-.66.64-1.32,1.3-2,2a12.92,12.92,0,0,1-1.42-2.2Z" fill="#fff"></path></g><path d="M0,0A45.3,45.3,0,0,0,8.37,10.62l.13.14h0l2.39,2.41a19,19,0,0,1-2.16,1.46l1,1,2.48-2.49A13.08,13.08,0,0,1,16,17l1-1a11.76,11.76,0,0,1-3.82-3.77l2.48-2.5-1-1a12.92,12.92,0,0,1-1.42,2.2C11.63,9.29,10.1,7.76,8.52,6.32l0,0A45.48,45.48,0,0,0,0,0ZM17,0A45,45,0,0,0,9,5.85l.82.78,2-2.06.48.48-2,2,.88.85A37.65,37.65,0,0,0,17,0ZM5.13,4.57l7.22,7.27-.48.48L4.65,5.05ZM2.37,8.68l-1,1,2.48,2.5A11.76,11.76,0,0,1,0,16l1,1a13.08,13.08,0,0,1,3.75-3.84l2.48,2.49,1-1a19,19,0,0,1-2.16-1.46L8,11.24l-.89-.93-2,2-.48-.48,2-2L5.78,8.9c-.66.64-1.32,1.3-2,2a12.92,12.92,0,0,1-1.42-2.2Z" fill="#777"></path></g></g></svg>`;
    settingsButton.append(settingsIcon);
    const settingsLabel = document.createElement("span");
    settingsLabel.innerText = "Crime Settings";
    settingsButton.append(settingsLabel);
    pageLinks.append(settingsButton);
  }
  function injectSettingsPage(container) {
    container.classList.add("tornium-crimes-settings");
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
    oauthScopes.append("identity faction:crimes");
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
    GM_setValue(`${GM_PREFIX}:state`, oauthState);
    GM_setValue(`${GM_PREFIX}:codeVerifier`, oauthCodeVerifier);
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
    container.append(configSection);
    const configLegend = document.createElement("legend");
    configLegend.innerText = "Configuration";
    configSection.append(configLegend);
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
    infoScriptLink.innerHTML = `<strong>Link: </strong> <a href="https://github.com/Tornium/tornium/blob/master/userscripts/tornium-crimes.user.js">GitHub</a>`;
    infoScriptContainer.append(infoScriptLink);
    const infoScriptDocs = document.createElement("p");
    infoScriptDocs.innerHTML = `<strong>Documentation: </strong> <a href="https://docs.tornium.com/en/latest/reference/tornium-crimes.html">docs.tornium.com</a>`;
    infoScriptContainer.append(infoScriptDocs);
    const infoScriptTerms = document.createElement("p");
    infoScriptTerms.innerHTML = `<strong>Terms of Service: </strong> This userscript falls under Tornium's <a href="https://tornium.com/terms">Terms of Service</a> and <a href="https://tornium.com/privacy">Privacy Policy</a>.`;
    infoScriptContainer.append(infoScriptTerms);
    infoContainer.append(infoScriptContainer);
    container.append(infoContainer);
  }
  function injectSettingsStyles() {
    GM_addStyle(`
.tornium-crimes-settings {
margin-top: 10px;
}

.tornium-crimes-settings hr {
border: none;
border-top: 1px solid #444;
margin-top: 20px !important;
margin-bottom: 20px !important;
}

.tornium-crimes-settings fieldset {
border: 1px solid #555;
border-radius: 6px;
padding: 16px;
margin-bottom: 20px;
background: rgba(0, 0, 0, 0.25);
}

.tornium-crimes-settings legend {
font-size: 1.2rem;
font-weight: bold;
padding: 0 6px;
color: #fff;
}

.tornium-crimes-settings .torn-btn {
display: inline-block;
margin: 8px 6px 0 0;
}
`);
  }
  function deleteOAuthToken() {
    GM_deleteValue(`${GM_PREFIX}:access-token`);
    GM_deleteValue(`${GM_PREFIX}:access-token-expires`);
    window.location.reload();
  }

  // entrypoint.js
  log(`Loading userscript v${VERSION}${DEBUG ? " with debug" : ""}${CACHE_ENABLED ? " with cache" : ""}...`);
  var query = new URLSearchParams(document.location.search);
  function executeCrimes() {
    createSettingsButton();
    injectStyles();
    torniumFetch("user", { ttl: 1e3 * 60 * 60 }).then((identityData) => {
      return [identityData.factiontid, identityData.tid];
    }).then(([factionID, userID]) => {
      GM_setValue(`${GM_PREFIX}:userID`, userID);
      return Promise.all([
        torniumFetch(`faction/${factionID}/crime/member/${userID}/optimum`, { ttl: 60 }),
        userID,
        factionID,
        waitForElement(`#faction-crimes-root [class*="buttonsContainer__"]`)
      ]);
    }).then(([data, userID, factionID, memberSelectorContainer]) => {
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
    if (errorContainer == void 0 || errorContainerTitle == void 0) {
      log("Failed to load settings page: missing error container");
    } else {
      errorContainer.innerHTML = "";
      errorContainerTitle.innerText = "Tornium Crimes Settings";
      injectSettingsStyles();
      injectSettingsPage(errorContainer);
    }
  } else if (window.location.pathname == new URL(redirectURI).pathname && window.location.host == new URL(redirectURI).host) {
    const callbackParams = new URLSearchParams(window.location.search);
    const callbackState = callbackParams.get("state");
    const callbackCode = callbackParams.get("code");
    const localState = GM_getValue(`${GM_PREFIX}:state`);
    const localCodeVerifier = GM_getValue(`${GM_PREFIX}:codeVerifier`);
    if (callbackState === localState) {
      resolveToken(callbackCode, callbackState, localCodeVerifier);
      log("Succesfully authenticated the OAuth token");
    } else {
      unsafeWindow.alert("Invalid security state. Try again.");
      log("Callback state: " + callbackState);
      log("Local state: " + localState);
      window.location.href = "https://www.torn.com";
    }
  } else if (window.location.pathname.startsWith("/factions.php") && query.get("step") == "your" && window.location.hash == "#/tab=crimes" && !isAuthExpired()) {
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
})();
