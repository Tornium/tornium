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

                    reject();
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
