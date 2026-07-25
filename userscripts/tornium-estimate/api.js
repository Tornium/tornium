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
                    try {
                        responseJSON = JSON.parse(response.responseText);
                        response.responseType = "json";
                    } catch (err) {
                        console.log(response.responseText);
                        console.log(err);
                        reject(err);
                        return;
                    }
                }

                if (responseJSON.error !== undefined) {
                    // TODO: Replace check with WWW-Authenticate header
                    GM_deleteValue("tornium-estimate:access-token");
                    GM_deleteValue("tornium-estimate:access-token-expires");

                    // TODO: Determine how this could use .reject but still have the response processed normally
                    resolve(responseJSON);
                    return responseJSON;
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

export function limitConcurrency(limit) {
    let active = 0;
    const queue = [];

    const next = () => {
        if (active >= limit || queue.length === 0) return;

        const { fn, resolve, reject } = queue.shift();
        active++;
        fn().then(
            (value) => {
                active--;
                resolve(value);
                next();
            },
            (err) => {
                active--;
                reject(err);
                next();
            },
        );
    };

    return function run(fn) {
        return new Promise((resolve, reject) => {
            queue.push({ fn, resolve, reject });
            next();
        });
    };
}
