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

import {
    fairFight,
    formatEstimate,
    formatOAuthError,
    formatStats,
    formatTorniumError,
    relativeTime,
} from "./common.js";

export function createProfileContainer() {
    const parentContainer = document.querySelector("div.content-title");

    const container = document.createElement("div");
    container.classList.add("tornium-estimate-profile-container");
    container.style.marginTop = "10px";
    parentContainer.append(container);

    const statsElement = document.createElement("p");
    statsElement.innerText = "Stats: ";
    container.append(statsElement);

    const statsSpan = document.createElement("span");
    statsSpan.setAttribute("id", "tornium-estimate-profile-stats");
    statsSpan.innerText = "Loading...";
    statsElement.append(statsSpan);

    const estimateElement = document.createElement("p");
    estimateElement.innerText = "Estimate: ";
    container.append(estimateElement);

    const estimateSpan = document.createElement("span");
    estimateSpan.setAttribute("id", "tornium-estimate-profile-estimate");
    estimateSpan.innerText = "Loading...";
    estimateElement.append(estimateSpan);

    return [statsSpan, estimateSpan];
}

export function updateProfileStatsSpan(statsData, statsSpan) {
    console.log(statsData);

    if (statsData.error != undefined) {
        statsSpan.innerText = formatOAuthError(statsData);
    } else if (statsData.code != undefined) {
        statsSpan.innerText = formatTorniumError(statsData);
    } else {
        statsSpan.innerText = `${formatStats(statsData)} [${relativeTime(statsData.timestamp)}] (FF: ${fairFight(statsData.stat_score)})`;
    }
}

export function updateProfileEstimateSpan(estimateData, estimateSpan) {
    console.log(estimateData);

    if (estimateData.error != undefined) {
        estimateSpan.innerText = formatOAuthError(estimateData);
    } else if (estimateData.code != undefined) {
        estimateSpan.innerText = formatTorniumError(estimateData);
    } else {
        estimateSpan.innerText = `${formatEstimate(estimateData)} (FF: ${fairFight(estimateData.stat_score)})`;
    }
}
