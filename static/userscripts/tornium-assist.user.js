// ==UserScript==
// @name         Tornium Assist
// @namespace    https://tornium.com
// @version      1.0.1
// @description  Sent an assist request to applicable Discord servers
// @author       tiksan [2383326]
// @match        https://www.torn.com/loader.php?sid=attack*
// @match        https://www.torn.com/profiles.php?*
// @match        https://www.torn.com/factions.php*
// @match        https://www.torn.com/tornium/oauth/*/callback*
// @match        https://tornium.com/oauth/*/callback*
// @grant        GM_xmlhttpRequest
// @grant        GM_addStyle
// @grant        GM_getValue
// @grant        GM_setValue
// @grant        GM_deleteValue
// @connect      tornium.com
// @run-at       document-idle
// @downloadURL  https://raw.githubusercontent.com/Tornium/tornium-core/master/static/userscripts/tornium-assist.user.js
// @updateURL    https://raw.githubusercontent.com/Tornium/tornium-core/master/static/userscripts/tornium-assist.user.js
// @supportURL   https://discord.gg/pPcqTRTRyF
// @require     https://github.com/Kwack-Kwack/GMforPDA/raw/main/GMforPDA.user.js
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

"use strict";

const baseURL = "https://tornium.com";
const clientID = "809be3486c11af540a3258dd3c31185c08f9518abcd08f4e";

let assistsViewerInterval = null;

function arrayToString(array) {
    return btoa(String.fromCharCode.apply(null, array)).replaceAll("=", "").replaceAll("+", "-").replaceAll("/", "_");
}

if (window.location.pathname.includes("/oauth/") && window.location.pathname.endsWith("/callback")) {
    let params = new URLSearchParams(window.location.search);

    if (params.get("state") != GM_getValue("tornium-assists:state")) {
        unsafeWindow.alert("Invalid State");
        console.log("invalid state");
        return;
    }

    let data = new URLSearchParams();
    data.set("code", params.get("code"));
    data.set("grant_type", "authorization_code");
    data.set("scope", "identity");
    data.set(
        "redirect_uri",
        "###PDA-APIKEY###".toString().startsWith("###")
            ? `${baseURL}/oauth/${clientID}/callback`
            : `https://www.torn.com/tornium/oauth/${clientID}/callback`
    );
    data.set("client_id", clientID);
    data.set("code_verifier", GM_getValue("tornium-assists:codeVerifier"));

    GM_xmlhttpRequest({
        method: "POST",
        url: `${baseURL}/oauth/token`,
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data: data.toString(),
        responseType: "json",
        onload: (response) => {
            console.log(response);
            if (response.responseType === undefined) {
                response.response = JSON.parse(response.responseText);
                response.responseType = "json";
            }

            let accessToken = response.response.access_token;
            let expiresAt = Math.floor(Date.now() / 1000) + response.response.expires_in;

            GM_setValue("tornium-assists:access-token", accessToken);
            GM_setValue("tornium-assists:access-token-expires", expiresAt);

            if ("###PDA-APIKEY###".toString().startsWith("###")) {
                unsafeWindow.location.href = "https://torn.com";
            }
        },
    });
    return;
}

const accessToken = GM_getValue("tornium-assists:access-token", null);
const accessTokenExpiration = GM_getValue("tornium-assists:access-token-expires", 0);

if (
    window.location.pathname.startsWith("/profiles.php") &&
    (accessToken === null || accessTokenExpiration <= Math.floor(Date.now() / 1000))
) {
    const state = arrayToString(window.crypto.getRandomValues(new Uint8Array(24)));
    const codeVerifier = arrayToString(window.crypto.getRandomValues(new Uint8Array(48)));
    GM_setValue("tornium-assists:state", state);
    GM_setValue("tornium-assists:codeVerifier", codeVerifier);

    let codeChallenge = await window.crypto.subtle.digest("SHA-256", new TextEncoder().encode(codeVerifier));
    codeChallenge = arrayToString(new Uint8Array(codeChallenge));

    const redirectURI = "###PDA-APIKEY###".toString().startsWith("###")
        ? `${baseURL}/oauth/${clientID}/callback`
        : `https://www.torn.com/tornium/oauth/${clientID}/callback`;
    const authorizeURL = `${baseURL}/oauth/authorize?response_type=code&client_id=${clientID}&state=${state}&scope=torn_key:usage faction:assists&code_challenge_method=S256&code_challenge=${codeChallenge}&redirect_uri=${redirectURI}`;

    $(".content-title").append(
        $(`<a class='torn-btn' id='tornium-authenticate' href='${authorizeURL}'>Signed Out - Authenticate</a>`)
    );
    return;
}

function forwardAssist(smokes, tears, heavies) {
    let defenderID = new URLSearchParams(location.search).get("user2ID");
    let requesterID = JSON.parse(document.getElementById("websocketConnectionData").innerText).userID;

    let request = GM_xmlhttpRequest({
        method: "POST",
        url: `${baseURL}/api/v1/faction/assist/${defenderID}`,
        data: JSON.stringify({
            smokes: smokes,
            tears: tears,
            heavies: heavies,
        }),
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${accessToken}`,
        },
        onload: (response) => {
            if (response.responseType === undefined) {
                response.response = JSON.parse(response.responseText);
                response.responseType = "json";
            }

            if (response.response.error !== undefined) {
                GM_deleteValue("tornium-assists:access-token");
                GM_deleteValue("tornium-assists:access-token-expires");

                document.getElementById("tornium-assist-status").textContent =
                    `[${response.response.error}] OAuth Error - ${response.response.error_description}`;
                return;
            }

            console.log(response.response);

            if (response.response.code !== undefined) {
                document.getElementById("tornium-assist-status").textContent =
                    `[${response.response.code}] ${response.response.name}: - ${response.response.message}...`;
                return;
            } else {
                document.getElementById("tornium-assist-status").textContent = "Unknown server error";
            }
        },
    });
}

function forwardAssistNormal() {
    let smokes = parseInt(document.getElementById("tornium-assist-smokes").value);
    let tears = parseInt(document.getElementById("tornium-assist-tears").value);
    let heavies = parseInt(document.getElementById("tornium-assist-heavies").value);
    forwardAssist(smokes, tears, heavies);
}

function forwardAssistQuick() {
    forwardAssist(0, 0, 0);
}

function checkAssists() {
    GM_xmlhttpRequest({
        method: "GET",
        url: `${baseURL}/api/v1/faction/assists`,
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${accessToken}`,
        },
        onload: (response) => {
            console.log(
                [
                    response.status,
                    response.statusText,
                    response.readyState,
                    response.responseHeaders,
                    response.responseText,
                    response.finalUrl,
                ].join("\n")
            );

            // {"5b35b6c53ee34cdaad20efa5cdc8e327":{"heavies":0,"requester":{"name":"tiksan","tid":2383326},"smokes":0,"target":{"faction":"New Sith Order [15644]","level":100,"name":"Comrade_Joe","tid":1691447},"tears":0}}

            let jsonResponse = JSON.parse(response.responseText);
            let container = $("#tornium-assists-viewer");
            container.empty();

            if ("code" in jsonResponse) {
                container.innerText = `ERROR: ${jsonResponse["message"]} [${jsonResponse["code"]}]`;
                return;
            }

            let table = $("<table>", {
                style: "width: 100%; border-collapse: collapse; table-layout: fixed; padding-top: 2px;",
            });
            table.append(
                $("<thead>").append(
                    $("<tr>").append([
                        $("<th>", {
                            text: "Requester",
                        }),
                        $("<th>", {
                            text: "Target",
                        }),
                        $("<th>", {
                            text: "Target Faction",
                        }),
                        $("<th>", {
                            text: "Smokes",
                        }),
                        $("<th>", {
                            text: "Tears",
                        }),
                        $("<th>", {
                            text: "Heavies",
                        }),
                    ])
                )
            );

            let tableBody = $("<tbody>");

            for (const [guid, assistRequest] of Object.entries(jsonResponse)) {
                let row = $("<tr>");
                row.append([
                    $("<td>", {
                        text: assistRequest.requester.name,
                        class: "tornium-text",
                    }),
                    $("<td>").append(
                        $("<a>", {
                            text: assistRequest.target.name,
                            href: `https://www.torn.com/loader.php?sid=attack&user2ID=${assistRequest.target.tid}`,
                            class: "tornium-text",
                        })
                    ),
                    $("<td>", {
                        text: assistRequest.target.faction,
                        class: "tornium-text",
                    }),
                    $("<td>").append(
                        $("<a>", {
                            class: "tornium-text",
                            text: `${assistRequest.smokes}x smokes`,
                            href: `https://tornium.com/faction/assists/${guid}?mode=smoke`,
                        })
                    ),
                    $("<td>").append(
                        $("<a>", {
                            class: "tornium-text",
                            text: `${assistRequest.tears}x tears`,
                            href: `https://tornium.com/faction/assists/${guid}?mode=tear`,
                        })
                    ),
                    $("<td>").append(
                        $("<a>", {
                            class: "tornium-text",
                            text: `${assistRequest.heavies}x heavies`,
                            href: `https://tornium.com/faction/assists/${guid}?mode=heavy`,
                        })
                    ),
                ]);

                tableBody.append(row);
            }
            table.append(tableBody);
            container.append(table);
        },
    });
}

function createAssistsViewer(warsContainer) {
    let assistsOuterContainer = document.createElement("ul");
    assistsOuterContainer.classList.add("f-war-list", "war-new");
    warsContainer.insertAdjacentElement("afterend", assistsOuterContainer);

    let seperator = document.createElement("hr");
    seperator.classList.add("delimiter-999", "m-top10");
    assistsOuterContainer.insertAdjacentElement("beforebegin", seperator);

    let assistsContainerHeader = document.createElement("div");
    assistsContainerHeader.classList.add("title-black", "title-toggle", "m-top10", "tablet", "active", "top-round");
    assistsContainerHeader.setAttribute("data-title", "tornium-assists-viewer");
    assistsContainerHeader.role = "heading";
    assistsContainerHeader.textContent = "Tornium Assists";
    assistsOuterContainer.appendChild(assistsContainerHeader);

    let assistsContainer = document.createElement("li");
    assistsContainer.classList.add("description", "first-in-row", "tornium-assists-viewer");
    assistsContainer.id = "tornium-assists-viewer";
    assistsContainer.style.width = "100%";
    assistsContainer.style.marginTop = "0px";
    assistsOuterContainer.appendChild(assistsContainer);

    let assistsClear = document.createElement("li");
    assistsClear.classList.add("clear");
    assistsOuterContainer.appendChild(assistsClear);

    checkAssists();
    window.setInterval(checkAssists, 10000); // 10 seconds
}

if (location.pathname == "/loader.php" && location.search.includes("sid=attack")) {
    let container = document.createElement("div");
    container.style.display = "flex";
    container.style.justifyContent = "space-between";
    container.style.alignItems = "center";
    let topSection = $('[class*="topSection"]');
    topSection.parent().prepend(container);

    let quickAssistButton = document.createElement("button");
    quickAssistButton.classList.add("torn-btn");
    quickAssistButton.textContent = "Quick Assist";
    container.appendChild(quickAssistButton);
    quickAssistButton.addEventListener("click", forwardAssistQuick);

    let statusSpan = document.createElement("span");
    statusSpan.style.margin = "2em";
    statusSpan.textContent = "Status: Ready...";
    statusSpan.id = "tornium-assist-status";
    container.appendChild(statusSpan);

    let assistContainer = document.createElement("div");
    container.appendChild(assistContainer);

    let smokesInputLabel = document.createElement("label");
    smokesInputLabel.textContent = "Smokes:";
    smokesInputLabel.style.margin = "1em";
    assistContainer.appendChild(smokesInputLabel);

    let smokesInput = document.createElement("input");
    smokesInput.value = 0;
    smokesInput.min = 0;
    smokesInput.max = 10;
    smokesInput.style.width = "2em";
    smokesInput.style.textAlign = "center";
    smokesInput.inputmode = "numeric";
    smokesInput.classList.add("amount");
    smokesInput.id = "tornium-assist-smokes";
    assistContainer.appendChild(smokesInput);

    let tearsInputLabel = document.createElement("label");
    tearsInputLabel.textContent = "Tears:";
    tearsInputLabel.style.margin = "1em";
    assistContainer.appendChild(tearsInputLabel);

    let tearsInput = document.createElement("input");
    tearsInput.value = 0;
    tearsInput.min = 0;
    tearsInput.max = 10;
    tearsInput.style.width = "2em";
    tearsInput.style.textAlign = "center";
    tearsInput.inputmode = "numeric";
    tearsInput.classList.add("amount");
    tearsInput.id = "tornium-assist-tears";
    assistContainer.appendChild(tearsInput);

    let heaviesInputLabel = document.createElement("label");
    heaviesInputLabel.textContent = "Heavies:";
    heaviesInputLabel.style.margin = "1em";
    assistContainer.appendChild(heaviesInputLabel);

    let heaviesInput = document.createElement("input");
    heaviesInput.value = 0;
    heaviesInput.min = 0;
    heaviesInput.max = 10;
    heaviesInput.style.width = "2em";
    heaviesInput.style.textAlign = "center";
    heaviesInput.inputmode = "numeric";
    heaviesInput.classList.add("amount");
    heaviesInput.id = "tornium-assist-heavies";
    assistContainer.appendChild(heaviesInput);

    let assistButton = document.createElement("button");
    assistButton.classList.add("torn-btn");
    assistButton.style.margin = "1em";
    assistButton.textContent = "Request Assist";
    assistContainer.appendChild(assistButton);
    assistButton.addEventListener("click", forwardAssistNormal);
} else if (location.pathname == "/factions.php" && location.search.includes("step=your") && location.hash == "#/") {
    console.log("starting observer");
    let warsObserver = new MutationObserver(function (mutations, observer) {
        let warsElement = document.getElementById("faction_war_list_id");

        if (warsElement !== null) {
            console.log("element exists");
            observer.disconnect();
            createAssistsViewer(warsElement);
            return;
        }
    });

    warsObserver.observe(document.getElementsByClassName("content-wrapper")[0], {
        childList: true,
        subtree: true,
    });
}

GM_addStyle(`
.tornium-text {
    mix-blend-mode: difference;
    filter: invert(1);
}
`);
