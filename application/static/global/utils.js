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
    if (typeof timestamp === "string" && new Date(timestamp) !== "Invalid Date") {
        timestamp = Date.parse(timestamp) / 1000;
    }

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

function ready(callback) {
    if (document.readyState != "loading") {
        callback();
    } else {
        document.addEventListener("DOMContentLoaded", callback);
    }
}

function debounce(func, delay) {
    let timer;
    return function (...args) {
        clearTimeout(timer);
        timer = setTimeout(() => func.apply(this, args), delay);
    };
}

function parseIntArray(inputString) {
    if (inputString == "" || inputString == null) {
        return [];
    } else if (!inputString.startsWith("[") || !inputString.endsWith("]")) {
        return [];
    }

    inputString = inputString.slice(1, -1).trim();

    const numbers = inputString.split(",").map((num) => num.trim());
    const result = [];

    for (const num of numbers) {
        if (num == "") {
            continue;
        }

        result.push(num);
    }

    return result;
}

function parseStringArray(inputString) {
    if (inputString == "") {
        return [];
    } else if (!inputString.startsWith("[") || !inputString.endsWith("]")) {
        return [];
    }

    inputString = inputString.slice(1, -1).trim();

    const strings = inputString.split(",").map((str) => str.trim());
    const result = [];

    for (let string of strings) {
        if (string == "") {
            continue;
        } else if (string.startsWith("'") && string.endsWith("'")) {
            string = string.slice(1, -1).trim();
        } else if (string.startsWith('"') && string.endsWith('"')) {
            string = string.slice(1, -1).trim();
        }

        result.push(string);
    }

    return result;
}
