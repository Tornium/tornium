// ==UserScript==
// @name         Tornium Retalations
// @version      0.1.0-dev
// @copyright    GPLv3
// @author       tiksan [2383326]
// @match        https://www.torn.com/profiles.php*
// @match        https://tornium.com/oauth/6be7696c40837f83e5cab139e02e287408c186939c10b025/callback*
// @match        https://www.torn.com/tornium/oauth/6be7696c40837f83e5cab139e02e287408c186939c10b025/callback*
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
  var DEBUG = true;
  GM_setValue("tornium-retaliations:test", "1");
  var clientLocalGM = localStorage.getItem("tornium-retaliations:test") === "1";

  // logging.js
  function log(string) {
    if (!DEBUG) {
      return;
    }
    console.log("[Tornium Retaliations] " + string);
  }

  // oauth.js
  var accessToken = GM_getValue("tornium-retaliations:access-token", null);
  var accessTokenExpiration = GM_getValue("tornium-retaliations:access-token-expires", 0);
  function isAuthExpired() {
    if (accessToken == null || accessTokenExpiration == 0) {
      return true;
    } else if (Math.floor(Date.now() / 1e3) >= accessTokenExpiration) {
      return true;
    }
    return false;
  }

  // settings.js
  function createSettingsButton() {
    if (!window.pathname.startsWith("/faction.php")) {
      return;
    }
    const pageTitleElement = window.getElementById("skip-to-content");
    if (pageTitleElement == void 0) {
      log("Missing page title element");
      return;
    }
    const settingsButton = document.createElement("a");
    settingsButton.classList.add("t-clear");
    pageTitleElement.after(settingsButton);
  }

  // entrypoint.js
  log(`Loading userscript${DEBUG ? " with debug" : ""}...`);
  if (!isAuthExpired()) {
    log("Access token has expired and needs to be set again.");
  } else {
    createSettingsButton();
  }
})();
