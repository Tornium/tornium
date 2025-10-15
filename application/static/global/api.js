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

const csrfToken = document.currentScript.getAttribute("data-csrf-token");

function _tfetch(method, endpoint, { body, errorTitle, errorHandler }) {
    return window
        .fetch(endpoint, {
            method: method,
            headers: {
                "Content-Type": "application/json",
                "X-CSRF-Token": csrfToken,
            },
            ...(body !== undefined && { body: JSON.stringify(body) }),
        })
        .then(async (response) => {
            if (response.status == 204) {
                return 204;
            }

            try {
                return await response.json();
            } catch {
                generateToast("Tornium Error", "The Tornium API failed to respond with a parsable response.", "error");
                return Promise.reject();
            }
        })
        .then((jsonResponse) => {
            if (jsonResponse == 204) {
                return;
            } else if (jsonResponse.code !== undefined) {
                if (
                    errorHandler === undefined &&
                    (jsonResponse.details === undefined || jsonResponse.details.message === undefined)
                ) {
                    generateToast(
                        errorTitle === undefined ? "Tornium Error" : errorTitle,
                        `[${jsonResponse.code}] ${jsonResponse.message}`,
                        "error",
                    );
                } else if (
                    errorHandler === undefined &&
                    jsonResponse.details !== undefined &&
                    jsonResponse.details.message !== undefined
                ) {
                    generateToast(
                        errorTitle === undefined ? "Tornium Error" : errorTitle,
                        `[${jsonResponse.code}] ${jsonResponse.message}<br /><br />${jsonResponse.details.message}`,
                        "error",
                    );
                } else {
                    errorHandler(jsonResponse);
                }

                return Promise.reject();
            }

            return jsonResponse;
        });
}

function tfetch(method, endpoint, { body, errorTitle, errorHandler }) {
    return tfetch(method, `/api/v1/${endpoint}`, { body, errorTitle, errorHandler });
}
