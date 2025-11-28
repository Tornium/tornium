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

import { Config } from "../config.js";

function commas(value) {
    if (value === null) {
        return "Unknown";
    }

    return value.toLocaleString("en-US");
}

function shortNum(value) {
    return Intl.NumberFormat("en-us", { notation: "compact", maximumFractionDigits: 1 }).format(value);
}

export function formatStats(statsData) {
    const formatter = Config.exactStat ? commas : shortNum;

    return `${formatter(statsData.min)} to ${formatter(statsData.max)}`;
}

export function formatEstimate(estimateData) {
    const formatter = Config.exactStat ? commas : shortNum;

    return `${formatter(estimateData.min_bs)} to ${formatter(estimateData.max_bs)}`;
}

export function formatOAuthError(responseJSON) {
    return `[${responseJSON.error}] OAuth Error - ${responseJSON.error_description}`;
}

export function formatTorniumError(responseJSON) {
    return `[${responseJSON.code}] Tornium Error - ${responseJSON.message}`;
}

// Derived from https://stackoverflow.com/a/53800501/12941872
const TIME_UNITS = {
    // For use in the relative time function
    year: 24 * 60 * 60 * 1000 * 365,
    month: (24 * 60 * 60 * 1000 * 365) / 12,
    day: 24 * 60 * 60 * 1000,
    hour: 60 * 60 * 1000,
    minute: 60 * 1000,
    second: 1000,
};
const rtf = new Intl.RelativeTimeFormat("en", { numeric: "auto" });
export function relativeTime(timestamp) {
    const elapsed = timestamp * 1000 - Date.now();

    // "Math.abs" accounts for both "past" & "future" scenarios
    for (var u in TIME_UNITS) {
        if (Math.abs(elapsed) > TIME_UNITS[u] || u == "second") {
            return rtf.format(Math.round(elapsed / TIME_UNITS[u]), u);
        }
    }
}
