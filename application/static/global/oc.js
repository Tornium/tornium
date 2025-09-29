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

var ocNames = null;

function _writeOCNames() {
    const selector = document.getElementsByClassName("oc-name-selector");
    Array.from(selector).forEach(function (element) {
        ocNames.forEach((ocName) => {
            const option = document.createElement("option");
            option.value = ocName;
            option.textContent = ocName;
            element.append(option);
        });
    });
}

// TODO: Convert to caching the request instead of the request's data
// See tornium-estimate.user.js
let ocNamesRequest = (obj) => {
    var localOCNames = JSON.parse(localStorage.getItem("ocNames"));

    if (localOCNames && Math.floor(Date.now() / 1000) - localOCNames.timestamp < 3600) {
        return new Promise((resolve, reject) => {
            ocNames = localOCNames.ocNames;
            _writeOCNames();
            resolve();
        });
    } else {
        return new Promise((resolve, reject) => {
            tfetch("GET", "faction/crime/names", { errorTitle: "OC Names Not Loaded" }).then((response) => {
                ocNames = response;
                _writeOCNames();
                localStorage.setItem(
                    "ocNames",
                    JSON.stringify({
                        timestamp: Math.floor(Date.now() / 1000),
                        ocNames: ocNames,
                    }),
                );
                resolve();
            });
        });
    }
};
