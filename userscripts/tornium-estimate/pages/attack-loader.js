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

import { waitForElement } from "../dom.js";
import { log } from "../logging.js";
import { updateProfileStatsSpan, updateProfileEstimateSpan } from "./profile.js";
import { getUserEstimate, getUserStats } from "../stats.js";

export function injectAttackLoaderStats(userID) {
    waitForElement(`div[class^="playersModelWrap_"] div[class^="dialog_"]`).then((container) => {
        const statsSpan = document.createElement("span");
        statsSpan.id = "tornium-estimate-user-attack-loader-span";
        statsSpan.innerText = "Loading...";
        container.append(statsSpan);

        injectStats(statsSpan, userID);
    });
}

function injectStats(statsSpan, userID) {
    getUserStats(userID).then((statsData) => {
        if (statsData.code === 1100) {
            // There is no data on this user. We want to use an estimate instead
            injectEstimate(statsSpan, userID);
        } else if (new Date(statsData.timestamp * 1000) <= Date.now() - 1000 * 60 * 60 * 24 * 30) {
            // The data is too old. We want to use an estimate instead
            injectEstimate(statsSpan, userID);
        } else {
            updateProfileStatsSpan(statsData, statsSpan);
        }
    });
}

function injectEstimate(statsSpan, userID) {
    getUserEstimate(userID).then((estimateData) => {
        updateProfileEstimateSpan(estimateData, statsSpan);
    });
}
