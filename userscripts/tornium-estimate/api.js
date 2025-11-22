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

import { CACHE_EXPIRATION, getCache, putCache } from "./cache.js";
import { BASE_URL } from "./constants.js";
import { accessToken } from "./oauth.js";

export function torniumFetch(endpoint, options = { method: "GET", ttl: CACHE_EXPIRATION }) {
    return new Promise(async (resolve, reject) => {
        const cachedResponse = await getCache(endpoint);

        if (cachedResponse != null && cachedResponse != undefined) {
            resolve(cachedResponse);
            return cachedResponse;
        }

        return GM_xmlhttpRequest({
            method: options.method,
            url: `${BASE_URL}/api/v1/${endpoint}`,
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${accessToken}`,
            },
            responseType: "json",
            onload: async (response) => {
                let responseJSON = response.response;

                if (response.responseType === undefined) {
                    responseJSON = JSON.parse(response.responseText);
                    response.responseType = "json";
                }

                if (responseJSON.error !== undefined) {
                    // TODO: Replace check with WWW-Authenticate header
                    GM_deleteValue("tornium-retaliations:access-token");
                    GM_deleteValue("tornium-retaliations:access-token-expires");

                    reject(responseJSON.error);
                    return;
                }

                if (!("code" in responseJSON)) {
                    putCache(endpoint, response, options.ttl);
                }

                resolve(responseJSON);
                return responseJSON;
            },
            onerror: (error) => {
                reject(error);
                return;
            },
        });
    });
}
