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

function getTID(string) {
    if (/^\d+$/.test(string)) {
        return parseInt(string);
    }

    const matches = string.match(/\[(.*?)\]/);

    if (matches) {
        return parseInt(matches[1]);
    } else {
        return 0;
    }
}

function commas(number) {
    if (number === null) {
        return "Unknown";
    }

    return number.toLocaleString("en-US");
}

// Derived from https://stackoverflow.com/a/53800501/12941872
const rtfUnits = {
    year: 24 * 60 * 60 * 1000 * 365,
    month: (24 * 60 * 60 * 1000 * 365) / 12,
    day: 24 * 60 * 60 * 1000,
    hour: 60 * 60 * 1000,
    minute: 60 * 1000,
    second: 1000,
};
const rtf = new Intl.RelativeTimeFormat("en", { numeric: "auto" });
function reltime(timestamp) {
    var elapsed = timestamp * 1000 - Date.now();

    // "Math.abs" accounts for both "past" & "future" scenarios
    for (var u in rtfUnits) {
        if (Math.abs(elapsed) > rtfUnits[u] || u == "second") {
            return rtf.format(Math.round(elapsed / rtfUnits[u]), u);
        }
    }
}

function tcttime(timestamp) {
    let tsAdded = new Date(timestamp * 1000);
    tsAdded = tsAdded.toUTCString();
    return tsAdded.substring(0, tsAdded.length - 3) + "TCT";
}

function bsRange(battlescore) {
    return [Math.floor(Math.pow(battlescore, 2) / 4), Math.floor(Math.pow(battlescore, 2) / 2.75)];
}
