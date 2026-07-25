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

import { CACHE_ENABLED } from "./constants.js";

const CACHE_NAME = "tornium-estimate-cache";
export const CACHE_EXPIRATION = 1000 * 60 * 60 * 24; // 1 day

export async function getCache(url) {
    const cache = await caches.open(CACHE_NAME);
    const cachedResponse = await cache.match(url);

    if (cachedResponse) {
        const expirationTime = new Date(parseInt(cachedResponse.headers.get("cache-expiry")));

        if (Date.now() < expirationTime) {
            return await cachedResponse.json();
        }

        await cache.delete(url);
    }

    return null;
}

export async function putCache(url, response, ttl = CACHE_EXPIRATION) {
    const headers = parseHeaders(response.responseHeaders);
    headers["cache-expiry"] = String(Date.now() + ttl);

    const cache = await caches.open(CACHE_NAME);
    await cache.put(url, new Response(response.responseText, { headers: headers }));
}

function parseHeaders(headerString) {
    let headers = {};

    headerString.split("\r\n").forEach((line) => {
        const [key, value] = line.split(": ").map((item) => item.trim());

        if (key && value) {
            headers[key] = value;
        }
    });

    return headers;
}
