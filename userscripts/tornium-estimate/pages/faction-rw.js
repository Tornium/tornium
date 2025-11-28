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
import {
    fairFight,
    formatEstimate,
    formatOAuthError,
    formatStats,
    formatTorniumError,
    relativeTime,
} from "./common.js";
import { waitForElement } from "../dom.js";
import { log } from "../logging.js";
import { getUserEstimate, getUserStats } from "../stats.js";

export function checkRankedWarToggleState(event) {
    // We need to ensure the element we're waiting on is far enough down the tree that the table will be inserted into the DOM 
    // before the callback is executed.
    waitForElement(`div.desc-wrap[class*="warDesc"] div.faction-war div.members-cont`, 2500).then((rankedWarDescription) => {
        // FIXME: rename variable
        console.log(rankedWarDescription);
        if (rankedWarDescription == null) {
            // This element only exists when the ranked war section has been toggled.
            return false;
        }

        document.querySelectorAll(`div.level[class*="level_"]`).forEach(transformRankedWarLevelNode);
    });
}

const concurrencyLimiter = limitConcurrency(10);

function transformRankedWarLevelNode(node) {
    if (node.innerText == "Level") {
        // This is the node in the header in the table.
        node.innerText = "FF";
        return;
    }

    const userLinkNode = node.parentElement.querySelector(`div[class*="userInfoBox_"] div[class^="honorWrap_"] a[class^="linkWrap_"]`);
    const userLink = new URL(userLinkNode.href);
    const userLinkSearch = new URLSearchParams(userLink.search);
    const userID = userLinkSearch.get("XID");

    if (userID == null) {
        node.innerText = "ERR";
        return;
    }

    node.innerText = "...";

    concurrencyLimiter(() => {
        return getUserStats(userID);
    }).then((statsData) => {
        if (statsData.error != undefined) {
            log(`OAuth Error: ${statsData.error_description}`);
            node.innerText = `ERR`;
        } else if (statsData.code === 1100) {
            // There is no data on this user. We want to use an estimate instead
            transformRankedWarLevelNodeEstimate(node, userID);
        } else if (statsData.code != undefined) {
            log(`Tornium Error: [${statsData.code}] - ${statsData.message}`);
            node.innerText = `ERR`;
        } else if (new Date(statsData.timestamp * 1000) > Date.now() - 1000 * 60 * 60 * 24 * 30) {
            node.innerText = fairFight(statsData.stat_score);
        } else {
            // The data is too old. We want to use an estimate instead
            transformRankedWarLevelNodeEstimate(node, userID);
        }
    });
}

function transformRankedWarLevelNodeEstimate(node, userID) {
    concurrencyLimiter(() => {
        return getUserEstimate(userID);
    }).then((estimateData) => {
        if (estimateData.error != undefined) {
            log(`OAuth Error: ${estimateData.error_description}`);
            node.innerText = `ERR`;
        } else if (estimateData.code === 1100) {
            // There is no data on this user
            node.innerText = "N/A";
        } else if (estimateData.code != undefined) {
            log(`Tornium Error: [${estimateData.code}] - ${estimateData.message}`);
            node.innerText = `ERR`;
        } else {
            node.innerText = fairFight(estimateData.stat_score);
        }
    });
}
