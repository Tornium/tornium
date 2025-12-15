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
import { waitForElement } from "../dom.js";
import { log } from "../logging.js";
import { getUserEstimate, getUserStats } from "../stats.js";

export function startAbroadUserListObserver() {
    window.addEventListener("hashchange", hashChangeCallback);

    hashChangeCallback();
    injectStyles();
}

function hashChangeCallback(event) {
    waitForElement("ul.users-list li.last").then(() => {
        // We want to wait until the last user has been added to ensure React has fully injected the DOM
        injectUpdatedHeader();
        const userNodes = document.querySelectorAll("li a.user.name");

        Array.from(userNodes).forEach((userNode) => {
            const userNodeContainer = userNode.closest("li");

            if (userNodeContainer == null) {
                return;
            }

            injectStats(userNodeContainer);
        });
    });
}

const concurrencyLimiter = limitConcurrency(10);

function injectStats(addedNode) {
    if (addedNode.nodeName.toLowerCase() != "li") {
        return;
    }

    const statContainer = addedNode.querySelector("div.center-side-bottom.left");

    if (statContainer == null) {
        return;
    }

    const userNode = addedNode.querySelector("a.user.name");
    const userURL = new URL(userNode.href);
    const userID = new URLSearchParams(userURL.search).get("XID");

    const statSpan = document.createElement("span");
    statSpan.classList.add("tornium-estimate-abroad-user-stat");
    statSpan.innerText = "...";
    statContainer.append(statSpan);

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
    GM_addStyle(".tornium-estimate-abroad-user-stat {font-size: 12px; padding-right: 10px; float: right;}");
    GM_addStyle(".tornium-estimate-abroad-header-right {float: right; padding-right: 10px;}");
}

function injectUpdatedHeader() {
    // Since we're not replacing an existing column with the fair fight, we want to inject the header into an existing column.
    const iconsHeader = document.querySelector("div.users-list-title div.icons-b");

    if (iconsHeader == null) {
        return;
    }

    const right = document.createElement("span");
    right.className = "tornium-estimate-abroad-header-right";
    right.textContent = "Fair Fight";
    iconsHeader.append(right);
}
