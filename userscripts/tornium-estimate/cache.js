const CACHE_ENABLED = "caches" in window;
const CACHE_NAME = "tornium-estimate-cache";
export const CACHE_EXPIRATION = 1000 * 15; // 15 seconds

export async function getCache(url) {
    const cache = await caches.open(CACHE_NAME);
    const cachedResponse = await cache.match(url);

    if (cachedResponse) {
        const cachedTime = new Date(cachedResponse.headers.get("date")).getTime();
        const expirationTime = new Date(cachedResponse.headers.get("cache-expiry")).getTime();
        const now = Date.now();

        if (now < expirationTime) {
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
