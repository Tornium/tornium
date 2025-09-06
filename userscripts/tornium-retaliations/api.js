import { BASE_URL } from "./constants.js";
import { accessToken } from "./oauth.js";

export function tornium_fetch(endpoint, options = { method: "GET" }) {
    return new Promise(async (resolve, reject) => {
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
                console.log(responseJSON);

                if (response.responseType === undefined) {
                    responseJSON = JSON.parse(response.responseText);
                    response.responseType = "json";
                }

                if (responseJSON.error !== undefined) {
                    // TODO: Replace check with WWW-Authenticate header
                    GM_deleteValue("tornium-retaliations:access-token");
                    GM_deleteValue("tornium-retaliations:access-token-expires");

                    $("#tornium-estimation").text(
                        `[${responseJSON.error}] OAuth Error - ${responseJSON.error_description}`,
                    );
                    reject();
                    return;
                }

                resolve(responseJSON);
                return;
            },
            onerror: (error) => {
                reject(error);
                return;
            },
        });
    });
}
