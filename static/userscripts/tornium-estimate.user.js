// ==UserScript==
// @name         Tornium Estimation
// @namespace    https://tornium.com
// @version      0.3.1
// @copyright    AGPL
// @author       tiksan [2383326]
// @match        https://www.torn.com/profiles.php*
// @match        https://tornium.com/oauth/6be7696c40837f83e5cab139e02e287408c186939c10b025/callback*
// @match        https://www.torn.com/tornium/oauth/6be7696c40837f83e5cab139e02e287408c186939c10b025/callback*
// @grant        GM_xmlhttpRequest
// @grant        GM_getValue
// @grant        GM_setValue
// @grant        GM_deleteValue
// @connect      tornium.com
// @downloadURL  https://raw.githubusercontent.com/Tornium/tornium-core/master/static/userscripts/tornium-estimate.user.js
// @updateURL    https://raw.githubusercontent.com/Tornium/tornium-core/master/static/userscripts/tornium-estimate.user.js
// @supportURL   https://discord.gg/pPcqTRTRyF
// ==/UserScript==

/* Copyright (C) 2021-2023 tiksan

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>. */

const baseURL = "https://tornium.com";
const clientID = "6be7696c40837f83e5cab139e02e287408c186939c10b025";

// Tampermonkey will store data from GM_setValue separately, but TPDA and violentmonkey will store this in localstorage
GM_setValue("tornium:test", "1");
const clientLocalGM = localStorage.getItem("tornium:test") !== null;

function arrayToString(array) {
    return btoa(String.fromCharCode.apply(null, array)).replaceAll("=", "").replaceAll("+", "-").replaceAll("/", "_");
}

(async function () {
    "use strict";

    if (
        window.location.pathname == "/oauth/6be7696c40837f83e5cab139e02e287408c186939c10b025/callback" ||
        window.location.pathname == "/tornium/oauth/6be7696c40837f83e5cab139e02e287408c186939c10b025/callback"
    ) {
        let params = new URLSearchParams(window.location.search);

        if (params.get("state") !== GM_getValue("tornium:state")) {
            console.log("invalid state");
            unsafeWindow.alert("Invalid State");
            window.location.href = "https://torn.com";
            return;
        }

        let data = new URLSearchParams();
        data.set("code", params.get("code"));
        data.set("grant_type", "authorization_code");
        data.set("scope", "identity");
        data.set("client_id", clientID);
        data.set("code_verifier", GM_getValue("tornium:codeVerifier"));
        data.set(
            "redirect_uri",
            clientLocalGM
                ? `https://www.torn.com/tornium/oauth/${clientID}/callback`
                : `${baseURL}/oauth/${clientID}/callback`
        );

        console.log(data);

        GM_xmlhttpRequest({
            method: "POST",
            url: `${baseURL}/oauth/token`,
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data: data.toString(),
            responseType: "json",
            onload: (response) => {
                let responseJSON = response.response;

                if (response.responseType === undefined) {
                    responseJSON = JSON.parse(response.responseText);
                    response.responseType = "json";
                }

                console.log(responseJSON);

                let accessToken = responseJSON.access_token;
                let expiresAt = Math.floor(Date.now() / 1000) + responseJSON.expires_in;

                GM_setValue("tornium:access-token", accessToken);
                GM_setValue("tornium:access-token-expires", expiresAt);

                if (clientLocalGM) {
                    window.location.href = "https://torn.com";
                }
            },
        });
        return;
    }

    if (!window.location.href.startsWith("https://www.torn.com/profiles.php")) {
        return;
    }

    $(".content-title").append($("<p id='tornium-estimation'>Loading...</p>"));

    const accessToken = GM_getValue("tornium:access-token", null);
    const accessTokenExpiration = GM_getValue("tornium:access-token-expires", 0);

    if (accessToken === null || accessTokenExpiration <= Math.floor(Date.now() / 1000)) {
        const state = arrayToString(window.crypto.getRandomValues(new Uint8Array(24)));
        const codeVerifier = arrayToString(window.crypto.getRandomValues(new Uint8Array(48)));
        GM_setValue("tornium:state", state);
        GM_setValue("tornium:codeVerifier", codeVerifier);

        let codeChallenge = await window.crypto.subtle.digest("SHA-256", new TextEncoder().encode(codeVerifier));
        codeChallenge = arrayToString(new Uint8Array(codeChallenge));

        const redirectURI = clientLocalGM
            ? `https://www.torn.com/tornium/oauth/${clientID}/callback`
            : `${baseURL}/oauth/${clientID}/callback`;
        const authorizeURL = `${baseURL}/oauth/authorize?response_type=code&client_id=${clientID}&state=${state}&scope=torn_key:usage&code_challenge_method=S256&code_challenge=${codeChallenge}&redirect_uri=${redirectURI}`;

        $("#tornium-estimation").text("Signed out");
        $(".content-title").append(
            $(`<a class='torn-btn' id='tornium-authenticate' href='${authorizeURL}'>Authenticate</a>`)
        );
        return;
    }

    const search = new URLSearchParams(new URL(window.location).search);

    GM_xmlhttpRequest({
        method: "GET",
        url: `${baseURL}/api/v1/user/estimate/${search.get("XID")}`,
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${accessToken}`,
        },
        responseType: "json",
        onload: (response) => {
            let responseJSON = response.response;

            if (response.responseType === undefined) {
                responseJSON = JSON.parse(response.responseText);
                response.responseType = "json";
            }

            if (responseJSON.error !== undefined) {
                GM_deleteValue("tornium:access-token");
                GM_deleteValue("tornium:access-token-expires");

                $("#tornium-estimation").text(
                    `[${responseJSON.error}] OAuth Error - ${responseJSON.error_description}`
                );
                return;
            }

            console.log(responseJSON);
            if (responseJSON.code !== undefined) {
                $("#tornium-estimation").text(`[${responseJSON.code}] Failed to load - ${responseJSON.message}...`);
                return;
            }

            $("#tornium-estimation").text(
                `${responseJSON.min_bs.toLocaleString()} to ${responseJSON.max_bs.toLocaleString()}`
            );
        },
    });
})();
