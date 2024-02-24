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

const csrfToken = document.currentScript.getAttribute("data-csrf-token");

function tfetch(method, endpoint, { body, errorTitle }) {
    return window
        .fetch(`/api/v1/${endpoint}`, {
            method: method,
            headers: {
                "Content-Type": "application/json",
                "X-CSRF-Token": csrfToken,
            },
            ...(body !== undefined && { body: JSON.stringify(body) }),
        })
        .then(async (response) => {
            try {
                return await response.json();
            } catch {
                generateToast("Tornium Error", "The Tornium API failed to respond with a parsable response.", "error");
                return Promise.reject();
            }
        })
        .then((jsonResponse) => {
            if (jsonResponse.code !== undefined) {
                generateToast(
                    errorTitle === undefined ? "Tornium Error" : errorTitle,
                    `[${jsonResponse.code}] ${jsonResponse.message}`,
                    "error"
                );
                return Promise.reject();
            }

            return jsonResponse;
        });
}
