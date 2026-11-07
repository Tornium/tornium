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

import { log } from "./logging.js";
import { CACHE_ENABLED, CACHE_NAME } from "./constants.js";

export const CACHE_EXPIRATION = 1000 * 60 * 60 * 24; // 1 day
const CACHE_HEADER_KEYS = new Set(["content-encoding", "content-type", "date", "etag"]);

let cacheInstance = null;
async function getCacheInstance() {
    if (cacheInstance == null) {
        cacheInstance = await caches.open(CACHE_NAME);
    }

    return cacheInstance;
}

export async function getCache(url) {
    if (!CACHE_ENABLED) {
        return null;
    }

    const cache = await getCacheInstance();
    const cachedResponse = await cache.match(url);

    if (cachedResponse) {
        const expirationTime = new Date(parseInt(cachedResponse.headers.get("cache-expiry")));

        if (Date.now() < expirationTime) {
            log(`HIT ${url}`, true);
            return await cachedResponse.json();
        }

        log(`EXPIRE ${url}`, true);
        await cache.delete(url);
    }

    log(`MISS ${url}`, true);
    return null;
}

export async function putCache(url, response, ttl = CACHE_EXPIRATION) {
    if (!CACHE_ENABLED) {
        return null;
    }

    const newHeaders = new Headers();

    for (const line of (response.responseHeaders || "").trim().split(/[\r\n]+/)) {
        const seperatorIndex = line.indexOf(":");

        if (seperatorIndex <= 0) {
            continue;
        }

        const headerKey = line.slice(0, seperatorIndex).trim().toLowerCase();

        if (!CACHE_HEADER_KEYS.has(headerKey)) {
            continue;
        }

        newHeaders.set(headerKey, line.slice(0, seperatorIndex + 1).trim());
    }

    newHeaders.set("cache-expiry", String(Date.now() + ttl));

    const modifiedResponse = new Response(response.responseText, {
        status: response.status,
        statusText: response.statusText || "",
        headers: newHeaders,
    });

    const cache = await getCacheInstance();
    await cache.put(url, modifiedResponse);
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
