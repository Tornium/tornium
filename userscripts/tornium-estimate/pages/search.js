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

import { limitConcurrency } from "../api.js";
import { fairFight } from "./common.js";
import { clientMobile } from "../constants.js";
import { waitForElement } from "../dom.js";
import { log } from "../logging.js";
import { getUserEstimate, getUserStats } from "../stats.js";

export function startSearchUserListObserver() {
    window.addEventListener("hashchange", hashChangeCallback);

    hashChangeCallback();
    injectStyles();
}

function hashChangeCallback(event) {
    waitForElement(`ul.user-info-list-wrap li[class^="user"] div.expander`).then(() => {
        const userNodes = document.querySelectorAll(`li[class^="user"]`);
        Array.from(userNodes).forEach(injectStats);
    });
}

const concurrencyLimiter = limitConcurrency(10);

function injectStats(addedNode) {
    if (addedNode.nodeName.toLowerCase() != "li") {
        return;
    } else if ("last" in addedNode.classList) {
        return;
    }

    const userContainer = addedNode.querySelector(".expander");
    if (userContainer == null) {
        return;
    }

    const userNode = userContainer.querySelector(".user.name");
    const userURL = new URL(userNode.href);
    const userID = new URLSearchParams(userURL.search).get("XID");

    const statSpan = document.createElement("span");
    statSpan.classList.add("tornium-estimate-search-user-stat");
    statSpan.id = `tornium-estimate-search-user-stat-${userID}`;
    statSpan.innerText = "...";
    userContainer.append(statSpan);

    concurrencyLimiter(() => {
        return getUserStats(userID);
    }).then((statsData) => {
        if (statsData.error != undefined) {
            log(`OAuth Error: ${statsData.error_description}`);
            statSpan.innerText = `ERR`;
        } else if (statsData.code === 1100) {
            // There is no data on this user. We want to use an estimate instead
            injectEstimate(statSpan, userID);
        } else if (statsData.code != undefined) {
            log(`Tornium Error: [${statsData.code}] - ${statsData.message}`);
            statSpan.innerText = `ERR`;
        } else if (new Date(statsData.timestamp * 1000) > Date.now() - 1000 * 60 * 60 * 24 * 30) {
            statSpan.innerText = fairFight(statsData.stat_score);
        } else {
            // The data is too old. We want to use an estimate instead
            injectEstimate(statSpan, userID);
        }
    });
}

function injectEstimate(statSpan, userID) {
    concurrencyLimiter(() => {
        return getUserEstimate(userID);
    }).then((estimateData) => {
        if (estimateData.error != undefined) {
            log(`OAuth Error: ${estimateData.error_description}`);
            statSpan.innerText = `ERR`;
        } else if (estimateData.code === 1100) {
            // There is no data on this user
            statSpan.innerText = "N/A";
        } else if (estimateData.code != undefined) {
            log(`Tornium Error: [${estimateData.code}] - ${estimateData.message}`);
            statSpan.innerText = `ERR`;
        } else {
            statSpan.innerText = fairFight(estimateData.stat_score);
        }
    });
}

function injectStyles() {
    if (clientMobile) {
        GM_addStyle(
            ".tornium-estimate-search-user-stat {font-size: 12px; display: inline-block; right: 0px; position: absolute; padding-right: 40px;}",
        );
    } else {
        GM_addStyle(
            ".tornium-estimate-search-user-stat {font-size: 12px; display: inline-block; right: 0px; position: absolute; padding-right: 15px;}",
        );
    }
}
