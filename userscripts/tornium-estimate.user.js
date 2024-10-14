// ==UserScript==
// @name         Tornium Estimation
// @namespace    https://tornium.com
// @version      0.3.7
// @copyright    GPLv3
// @author       tiksan [2383326]
// @match        https://www.torn.com/profiles.php*
// @match        https://tornium.com/oauth/6be7696c40837f83e5cab139e02e287408c186939c10b025/callback*
// @match        https://www.torn.com/tornium/oauth/6be7696c40837f83e5cab139e02e287408c186939c10b025/callback*
// @match        https://www.torn.com/gym.php*
// @match        https://www.torn.com/loader.php?sid=attack*
// @match        https://www.torn.com/page.php?sid=UserList*
// @grant        GM_xmlhttpRequest
// @grant        GM_getValue
// @grant        GM_setValue
// @grant        GM_deleteValue
// @grant        GM_addStyle
// @connect      tornium.com
// @downloadURL  https://github.com/Tornium/tornium/raw/refs/heads/master/userscripts/tornium-estimate.user.js
// @updateURL    https://github.com/Tornium/tornium/raw/refs/heads/master/userscripts/tornium-estimate.user.js
// @supportURL   https://discord.gg/pPcqTRTRyF
// ==/UserScript==

/* Copyright (C) 2021-2023 tiksan

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

const BASE_URL = "https://tornium.com";
const CLIENT_ID = "6be7696c40837f83e5cab139e02e287408c186939c10b025";
const DEBUG = false;
const CACHE_ENABLED = "caches" in window;
const CACHE_NAME = "tornium-estimate-cache";
const CACHE_EXPIRATION = 1000 * 60 * 60 * 24 * 7; // 7 days
const TIME_UNITS = {
    // For use in the relative time function
    year: 24 * 60 * 60 * 1000 * 365,
    month: (24 * 60 * 60 * 1000 * 365) / 12,
    day: 24 * 60 * 60 * 1000,
    hour: 60 * 60 * 1000,
    minute: 60 * 1000,
    second: 1000,
};

// Code taken from https://stackoverflow.com/a/11381730/12941872
// biome-ignore format: This function isn't readable anyways
window.mobileCheck = function() {
  let check = false;
  (function(a){if(/(android|bb\d+|meego).+mobile|avantgo|bada\/|blackberry|blazer|compal|elaine|fennec|hiptop|iemobile|ip(hone|od)|iris|kindle|lge |maemo|midp|mmp|mobile.+firefox|netfront|opera m(ob|in)i|palm( os)?|phone|p(ixi|re)\/|plucker|pocket|psp|series(4|6)0|symbian|treo|up\.(browser|link)|vodafone|wap|windows ce|xda|xiino/i.test(a)||/1207|6310|6590|3gso|4thp|50[1-6]i|770s|802s|a wa|abac|ac(er|oo|s\-)|ai(ko|rn)|al(av|ca|co)|amoi|an(ex|ny|yw)|aptu|ar(ch|go)|as(te|us)|attw|au(di|\-m|r |s )|avan|be(ck|ll|nq)|bi(lb|rd)|bl(ac|az)|br(e|v)w|bumb|bw\-(n|u)|c55\/|capi|ccwa|cdm\-|cell|chtm|cldc|cmd\-|co(mp|nd)|craw|da(it|ll|ng)|dbte|dc\-s|devi|dica|dmob|do(c|p)o|ds(12|\-d)|el(49|ai)|em(l2|ul)|er(ic|k0)|esl8|ez([4-7]0|os|wa|ze)|fetc|fly(\-|_)|g1 u|g560|gene|gf\-5|g\-mo|go(\.w|od)|gr(ad|un)|haie|hcit|hd\-(m|p|t)|hei\-|hi(pt|ta)|hp( i|ip)|hs\-c|ht(c(\-| |_|a|g|p|s|t)|tp)|hu(aw|tc)|i\-(20|go|ma)|i230|iac( |\-|\/)|ibro|idea|ig01|ikom|im1k|inno|ipaq|iris|ja(t|v)a|jbro|jemu|jigs|kddi|keji|kgt( |\/)|klon|kpt |kwc\-|kyo(c|k)|le(no|xi)|lg( g|\/(k|l|u)|50|54|\-[a-w])|libw|lynx|m1\-w|m3ga|m50\/|ma(te|ui|xo)|mc(01|21|ca)|m\-cr|me(rc|ri)|mi(o8|oa|ts)|mmef|mo(01|02|bi|de|do|t(\-| |o|v)|zz)|mt(50|p1|v )|mwbp|mywa|n10[0-2]|n20[2-3]|n30(0|2)|n50(0|2|5)|n7(0(0|1)|10)|ne((c|m)\-|on|tf|wf|wg|wt)|nok(6|i)|nzph|o2im|op(ti|wv)|oran|owg1|p800|pan(a|d|t)|pdxg|pg(13|\-([1-8]|c))|phil|pire|pl(ay|uc)|pn\-2|po(ck|rt|se)|prox|psio|pt\-g|qa\-a|qc(07|12|21|32|60|\-[2-7]|i\-)|qtek|r380|r600|raks|rim9|ro(ve|zo)|s55\/|sa(ge|ma|mm|ms|ny|va)|sc(01|h\-|oo|p\-)|sdk\/|se(c(\-|0|1)|47|mc|nd|ri)|sgh\-|shar|sie(\-|m)|sk\-0|sl(45|id)|sm(al|ar|b3|it|t5)|so(ft|ny)|sp(01|h\-|v\-|v )|sy(01|mb)|t2(18|50)|t6(00|10|18)|ta(gt|lk)|tcl\-|tdg\-|tel(i|m)|tim\-|t\-mo|to(pl|sh)|ts(70|m\-|m3|m5)|tx\-9|up(\.b|g1|si)|utst|v400|v750|veri|vi(rg|te)|vk(40|5[0-3]|\-v)|vm40|voda|vulc|vx(52|53|60|61|70|80|81|83|85|98)|w3c(\-| )|webc|whit|wi(g |nc|nw)|wmlb|wonu|x700|yas\-|your|zeto|zte\-/i.test(a.substr(0,4))) check = true;})(navigator.userAgent||navigator.vendor||window.opera);
  return check;
};

// Tampermonkey will store data from GM_setValue separately, but TPDA and violentmonkey will store this in localstorage
GM_setValue("tornium-estimate:test", "1");
const clientLocalGM = localStorage.getItem("tornium-estimate:test") !== null;

const accessToken = GM_getValue("tornium-estimate:access-token", null);
const accessTokenExpiration = GM_getValue("tornium-estimate:access-token-expires", 0);
const userStatScore = GM_getValue("tornium-estimate:user:bs", null);

if (window.mobileCheck()) {
    GM_addStyle(
        ".tornium-estimate-inline {font-size: 12px; display: inline-block; right: 0px; position: absolute; padding-right: 40px;}",
    );
} else {
    GM_addStyle(
        ".tornium-estimate-inline {font-size: 12px; display: inline-block; right: 0px; position: absolute; padding-right: 15px;}",
    );
}

function arrayToString(array) {
    return btoa(String.fromCharCode.apply(null, array)).replaceAll("=", "").replaceAll("+", "-").replaceAll("/", "_");
}

// Derived from https://stackoverflow.com/a/53800501/12941872
const rtf = new Intl.RelativeTimeFormat("en", { numeric: "auto" });
function relativeTime(timestamp) {
    var elapsed = timestamp * 1000 - Date.now();

    // "Math.abs" accounts for both "past" & "future" scenarios
    for (var u in TIME_UNITS) {
        if (Math.abs(elapsed) > TIME_UNITS[u] || u == "second") {
            return rtf.format(Math.round(elapsed / TIME_UNITS[u]), u);
        }
    }
}

function shortNum(value) {
    return Intl.NumberFormat("en-us", { notation: "compact", maximumFractionDigits: 1 }).format(value);
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

function LOG(string) {
    if (DEBUG) {
        console.log(string);
    }
}

function tornium_fetch(url, options = { method: "GET" }) {
    return new Promise(async (resolve, reject) => {
        let cache;
        if (CACHE_ENABLED) {
            cache = await caches.open(CACHE_NAME);
            const cachedResponse = await cache.match(url);

            if (cachedResponse) {
                const cachedTime = new Date(cachedResponse.headers.get("date")).getTime();
                const now = Date.now();

                if (now - cachedTime < CACHE_EXPIRATION) {
                    LOG("Using cached value");
                    resolve(cachedResponse.json());
                    return;
                }

                LOG("Deleting expired cached value");
                await cache.delete(url);
            }
        }

        return GM_xmlhttpRequest({
            method: options.method,
            url: url,
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${accessToken}`,
            },
            responseType: "json",
            onload: async (response) => {
                let responseJSON = response.response;

                if (response.responseType === undefined) {
                    responseJSON = JSON.parse(response.responseText);
                    response.responseType = "json";
                }

                if (responseJSON.error !== undefined) {
                    GM_deleteValue("tornium-estimate:access-token");
                    GM_deleteValue("tornium-estimate:access-token-expires");

                    $("#tornium-estimation").text(
                        `[${responseJSON.error}] OAuth Error - ${responseJSON.error_description}`,
                    );
                    reject();
                    return;
                }

                if (CACHE_ENABLED && !("code" in responseJSON)) {
                    const headers = parseHeaders(response.responseHeaders);
                    await cache.put(url, new Response(response.responseText, { headers: headers }));
                }

                LOG(responseJSON);
                resolve(responseJSON);
                return;
            },
            onerror: (error) => {
                reject(error);
                return;
            },
        });
    });
}

async function getOneEstimate(tid) {
    const url = `${BASE_URL}/api/v1/user/estimate/${tid}`;
    return await tornium_fetch(url);
}

async function getOneStat(tid) {
    const url = `${BASE_URL}/api/v1/user/${tid}/stat`;
    return await tornium_fetch(url);
}

(async function () {
    "use strict";

    if (
        (window.location.host == "tornium.com" && window.location.pathname == `/oauth/${CLIENT_ID}/callback`) ||
        (window.location.host == "torn.com" && window.location.pathname == `/tornium/oauth/${CLIENT_ID}/callback`)
    ) {
        let params = new URLSearchParams(window.location.search);

        if (params.get("state") !== GM_getValue("tornium-estimate:state")) {
            LOG("invalid state");
            unsafeWindow.alert("Invalid State");
            window.location.href = "https://torn.com";
            return;
        }

        let data = new URLSearchParams();
        data.set("code", params.get("code"));
        data.set("grant_type", "authorization_code");
        data.set("scope", "identity");
        data.set("client_id", CLIENT_ID);
        data.set("code_verifier", GM_getValue("tornium-estimate:codeVerifier"));
        data.set(
            "redirect_uri",
            clientLocalGM
                ? `https://www.torn.com/tornium/oauth/${CLIENT_ID}/callback`
                : `${BASE_URL}/oauth/${CLIENT_ID}/callback`,
        );

        GM_xmlhttpRequest({
            method: "POST",
            url: `${BASE_URL}/oauth/token`,
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

                LOG(responseJSON);

                let accessToken = responseJSON.access_token;
                let expiresAt = Math.floor(Date.now() / 1000) + responseJSON.expires_in;

                GM_setValue("tornium-estimate:access-token", accessToken);
                GM_setValue("tornium-estimate:access-token-expires", expiresAt);

                window.location.href = "https://torn.com";
                return;
            },
        });
        return;
    }

    LOG(window.location.href);

    if (window.location.href.startsWith("https://www.torn.com/profiles.php")) {
        $(".content-title").append($("<p id='tornium-estimation'>Loading estimate...</p>"));
        $(".content-title").append($("<p id='tornium-stats'>Loading stats...</p>"));

        if (accessToken === null || accessTokenExpiration <= Math.floor(Date.now() / 1000)) {
            const state = arrayToString(window.crypto.getRandomValues(new Uint8Array(24)));
            const codeVerifier = arrayToString(window.crypto.getRandomValues(new Uint8Array(48)));
            GM_setValue("tornium-estimate:state", state);
            GM_setValue("tornium-estimate:codeVerifier", codeVerifier);

            let codeChallenge = await window.crypto.subtle.digest("SHA-256", new TextEncoder().encode(codeVerifier));
            codeChallenge = arrayToString(new Uint8Array(codeChallenge));

            const redirectURI = clientLocalGM
                ? `https://www.torn.com/tornium/oauth/${CLIENT_ID}/callback`
                : `${BASE_URL}/oauth/${CLIENT_ID}/callback`;
            const authorizeURL = `${BASE_URL}/oauth/authorize?response_type=code&client_id=${CLIENT_ID}&state=${state}&scope=torn_key:usage&code_challenge_method=S256&code_challenge=${codeChallenge}&redirect_uri=${redirectURI}`;

            $("#tornium-estimation").text("Signed out");
            $(".content-title").append(
                $(`<a class='torn-btn' id='tornium-authenticate' href='${authorizeURL}'>Authenticate</a>`),
            );
            return;
        }

        const search = new URLSearchParams(new URL(window.location).search);

        getOneEstimate(search.get("XID")).then((userEstimate) => {
            if (userEstimate.code !== undefined) {
                $("#tornium-estimation").text(
                    `[${userEstimate.code}] Failed to load estimate - ${userEstimate.message}...`,
                );
                return;
            }

            let ffString = "";
            if (userStatScore !== null) {
                ffString = (1 + ((8 / 3) * userEstimate.stat_score) / userStatScore).toFixed(2);
            }

            $("#tornium-estimation").text(
                `Estimate: ${userEstimate.min_bs.toLocaleString()} to ${userEstimate.max_bs.toLocaleString()} (FF: ${ffString})`,
            );
        });

        getOneStat(search.get("XID")).then((userStats) => {
            if (userStats.code !== undefined && userStats.code != 1100) {
                $("#tornium-stats").text(`[${userStats.code}] Failed to load stats - ${userStats.message}...`);
                return;
            } else if (userStats.code !== undefined && userStats.code == 1100) {
                $("#tornium-stats").text(`[1100] Failed to load stats - No data available for this user`);
                return;
            }

            let ffString = "";
            if (userStatScore !== null) {
                ffString = (1 + ((8 / 3) * userStats.stat_score) / userStatScore).toFixed(2);
            }

            $("#tornium-stats").text(
                `Stat DB: ${userStats.min.toLocaleString()} to ${userStats.max.toLocaleString()} [${relativeTime(
                    userStats.timestamp,
                )}] (FF: ${ffString})`,
            );
        });
    } else if (window.location.href.startsWith("https://www.torn.com/gym.php")) {
        const observer = new MutationObserver(function (mutationList, observer) {
            let statScore = 0;
            for (const mutation of mutationList) {
                if (
                    mutation.addedNodes.length == 0 ||
                    !mutation.target.className.toString().startsWith("properties__")
                ) {
                    // Currently, the parent element containing the elements for the individual stats is properties__
                    continue;
                }

                // Example inner text
                // Strength\n111,111,111\n\nDamage you make on impact\n\nUnavailable\n\nTRAIN

                if (mutation.addedNodes[0].innerText.startsWith("Strength") || mutation.addedNodes[0].innerText.startsWith("STR")) {
                    statScore += Math.sqrt(Number(mutation.addedNodes[0].innerText.split("\n")[1].replaceAll(",", "")));
                } else if (mutation.addedNodes[0].innerText.startsWith("Defense") || mutation.addedNodes[0].innerText.startsWith("DEF")) {
                    statScore += Math.sqrt(Number(mutation.addedNodes[0].innerText.split("\n")[1].replaceAll(",", "")));
                } else if (mutation.addedNodes[0].innerText.startsWith("Speed") || mutation.addedNodes[0].innerText.startsWith("SPD")) {
                    statScore += Math.sqrt(Number(mutation.addedNodes[0].innerText.split("\n")[1].replaceAll(",", "")));
                } else if (mutation.addedNodes[0].innerText.startsWith("Dexterity") || mutation.addedNodes[0].innerText.startsWith("DEX")) {
                    statScore += Math.sqrt(Number(mutation.addedNodes[0].innerText.split("\n")[1].replaceAll(",", "")));
                    GM_setValue("tornium-estimate:user:bs", statScore);
                    observer.disconnect();
                    return;
                }
            }
        });
        observer.observe(document.getElementById("gymroot"), { attributes: false, childList: true, subtree: true });
    } else if (window.location.href.startsWith("https://www.torn.com/loader.php?sid=attack")) {
        const observer = new MutationObserver(function (mutationList, observer) {
            for (const mutation of mutationList) {
                if (
                    mutation.addedNodes.length == 0 ||
                    !mutation.addedNodes[0].className.toString().startsWith("playersModelWrap__")
                ) {
                    continue;
                }

                $("div[class^='colored__']").append("<span id='tornium-estimation'>Loading...</span>");

                getOneEstimate(new URLSearchParams(new URL(window.location).search).get("user2ID")).then(
                    (userEstimate) => {
                        if (userEstimate.code !== undefined) {
                            $("#tornium-estimation").text(
                                `[${userEstimate.code}] Failed to load estimate - ${userEstimate.message}...`,
                            );
                            return;
                        }

                        let ffString = "";
                        if (userStatScore !== null) {
                            ffString = (1 + ((8 / 3) * userEstimate.stat_score) / userStatScore).toFixed(2);
                        }

                        $("#tornium-estimation").text(
                            `${shortNum(userEstimate.min_bs)} to ${shortNum(userEstimate.max_bs)} (FF: ${ffString})`,
                        );
                        observer.disconnect();
                        return;
                    },
                );
            }
        });
        observer.observe(document.getElementById("react-root"), { attributes: false, childList: true, subtree: true });
    } else if (window.location.href.startsWith("https://www.torn.com/page.php?sid=UserList")) {
        const observer = new MutationObserver(function (mutationList, observer) {
            for (const mutation of mutationList) {
                if (mutation.addedNodes.length == 0) {
                    continue;
                }

                for (const addedNode of mutation.addedNodes) {
                    if (addedNode.nodeName.toLowerCase() != "li") {
                        continue;
                    } else if ("last" in addedNode.classList) {
                        continue;
                    }

                    const userContainer = addedNode.getElementsByClassName("expander")[0];
                    const userID = new URLSearchParams(
                        new URL(userContainer.getElementsByClassName("user name")[0].href).search,
                    ).get("XID");

                    let span = document.createElement("p");
                    span.classList = ["tornium-estimate-inline"];
                    span.id = `tornium-estimate-${userID}`;
                    span.text = "...";
                    userContainer.append(span);

                    getOneEstimate(userID).then((userEstimate) => {
                        if (userEstimate.code !== undefined) {
                            $(`#tornium-estimate-${userID}`).text("ERR");
                            return;
                        }

                        if (userStatScore !== null) {
                            let ffString = (1 + ((8 / 3) * userEstimate.stat_score) / userStatScore).toFixed(2);
                            $(`#tornium-estimate-${userID}`).text(`${ffString}x`);
                        } else {
                            $(`#tornium-estimate-${userID}`).text("ERR");
                        }
                    });
                }
            }
        });
        observer.observe(document.getElementsByClassName("user-info-list-wrap")[0], {
            attributes: false,
            childList: true,
            subtree: true,
        });
    }
})();
