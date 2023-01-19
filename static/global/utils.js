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
    if((/^\d+$/.test(string))) {
        return parseInt(string);
    }

    const matches = string.match(/\[(.*?)\]/);

    if(matches) {
        return parseInt(matches[1]);
    } else {
        return 0;
    }
}


function commas(number) {
    return number.toLocaleString('en-US');
}


function reltime(timestamp) {
    let delta = Date.now() / 1000 - timestamp;

    if(delta < 60) {  // One minute
        return "Now";
    } else if(delta < 3600) {  // Sixty minutes
        return Math.round(delta/60) + " minutes ago";
    } else if(delta < 86400) {  // One day
        return Math.round(delta/3600) + " hours ago";
    } else if(delta < 2592000) {  // Thirty days
        return Math.round(delta/86400) + " days ago";
    } else if(delta < 31104000) {  // Twelve months
        return Math.round(delta/2592000) + " months ago";
    } else {
        return "A long time ago";
    }
}


function tcttime(timestamp) {
    let tsAdded = new Date(timestamp * 1000);
    tsAdded = tsAdded.toUTCString();
    return tsAdded.substring(0, tsAdded.length - 3) + "TCT"
}
