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

import { APP_ID, APP_SCOPE, BASE_URL, GM_PREFIX, clientLocalGM } from "./constants.js";
import { log } from "./logging.js";

export let accessToken = GM_getValue(`${GM_PREFIX}:access-token`, null);
export let accessTokenExpiration = GM_getValue(`${GM_PREFIX}:access-token-expires`, 0);
export const redirectURI = clientLocalGM
    ? `https://www.torn.com/tornium/${APP_ID}/oauth/callback`
    : `${BASE_URL}/oauth/${APP_ID}/callback`;

if (typeof GM_addValueChangeListener != "undefined") {
    // TPDA currently does not implement this aspect of GM. As such, we need to ensure
    // that this still works for TPDA without this GM function, but we should prefer
    // this over a naive version.
    // See https://www.tampermonkey.net/documentation.php?locale=en&q=GM_values#api:GM_addValueChangeListener
    GM_addValueChangeListener(`${GM_PREFIX}:access-token`, (key, old_value, new_value, remote) => {
        log("Pushing new value of access token from listener", true);
        accessToken = new_val;
    });
    GM_addValueChangeListener(`${GM_PREFIX}:access-token-expires`, (key, old_value, new_value, remote) => {
        log("Pushing new value of access token expiration from listener", true);
        accessTokenExpiration = new_val;
    });
}

export function isAuthExpired() {
    // To ensure that we're not reading stale data from a desynced tab, let us fetch these dynamically.
    const currentAccessToken = GM_getValue(`${GM_PREFIX}:access-token`, null);
    const currentAccessTokenExpiration = GM_getValue(`${GM_PREFIX}:access-token-expires`, 0);

    if (currentAccessToken == null || currentAccessTokenExpiration == 0) {
        // Access token not set
        return true;
    } else if (Math.floor(Date.now() / 1000) >= currentAccessTokenExpiration) {
        return true;
    }

    return false;
}

export function hasRefreshToken() {
    return GM_getValue(`${GM_PREFIX}:refresh-token`) != null;
}

export async function refreshToken() {
    const acquiredLock = await navigator.locks.request(
        `${GM_PREFIX}:refresh-token-lock`,
        { ifAvailable: true },
        async (lock) => {
            if (!lock) {
                log("Failed to achieve lock. Skipping...");
                return false;
            }

            await doRefreshToken();
            return true;
        },
    );

    if (!acquiredLock) {
        log("Failed to achieve lock. Waiting on current refresh to finish to release the lock...");

        // We want to have a duplicate lock on the same lock key so that we can be notified
        // when to release this lock and let the user continue with a new access token in the
        // other tabs.
        await navigator.locks.request(`${GM_PREFIX}:refresh-token-lock`, async () => {});

        log("Lock released.");
        accessToken = GM_getValue(`${GM_PREFIX}:access-token`, null);
        accessTokenExpiration = GM_getValue(`${GM_PREFIX}:access-token-expires`, 0);
    }
}

async function doRefreshToken() {
    const refreshToken = GM_getValue(`${GM_PREFIX}:refresh-token`);

    if (refreshToken == null) {
        return;
    }

    log("Attempting to refresh access token with the refresh token...");

    // We want to immediately delete the refresh token to ensure it's not reused as to
    // avoid triggering the code for multiple usages of a refresh token.
    GM_deleteValue(`${GM_PREFIX}:refresh-token`);

    const tokenData = new URLSearchParams();
    tokenData.set("grant_type", "refresh_token");
    tokenData.set("refresh_token", refreshToken);
    tokenData.set("scope", APP_SCOPE);
    tokenData.set("client_id", APP_ID);
    console.log(tokenData);

    return new Promise((resolve, reject) => {
        GM_xmlhttpRequest({
            method: "POST",
            url: `${BASE_URL}/oauth/token`,
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            data: tokenData.toString(),
            responseType: "json",
            onload: (response) => {
                resolveTokenCallback(response);
                log("Access token successfully refreshed");
                // TODO: Implement successful message

                resolve(response);
            },
            onerror: (error) => {
                log(`Failed to refresh token: ${error}`);
                reject(error);
            },
            ontimeout: () => {
                log("Failed to refresh token: Request timed out");
                reject(new Error("Refresh token request timed out"));
            },
        });
    });
}

export function authStatus() {
    if (accessToken == null) {
        return "Disconnected";
    } else if (isAuthExpired() && hasRefreshToken()) {
        return "Expired (refreshable)";
    } else if (isAuthExpired()) {
        return "Expired";
    } else if (hasRefreshToken()) {
        return "Connected (refreshable)";
    }

    return "Connected";
}

export function authorizationURL(oauthState, codeChallenge) {
    return `${BASE_URL}/oauth/authorize?response_type=code&client_id=${APP_ID}&state=${oauthState}&scope=${APP_SCOPE}&code_challenge_method=S256&code_challenge=${codeChallenge}&redirect_uri=${redirectURI}`;
}

export function resolveToken(code, state, codeVerifier) {
    const tokenData = new URLSearchParams();
    tokenData.set("code", code);
    tokenData.set("grant_type", "authorization_code");
    tokenData.set("scope", APP_SCOPE);
    tokenData.set("client_id", APP_ID);
    tokenData.set("code_verifier", codeVerifier);
    tokenData.set("redirect_uri", redirectURI);

    GM_xmlhttpRequest({
        method: "POST",
        url: `${BASE_URL}/oauth/token`,
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data: tokenData.toString(),
        responseType: "json",
        onload: (response) => {
            resolveTokenCallback(response);
            // To avoid introducing an open redirect vulnerability, we are just going to
            // redirect to Torn's home page.
            // See https://cheatsheetseries.owasp.org/cheatsheets/Unvalidated_Redirects_and_Forwards_Cheat_Sheet.html
            window.location.href = "https://www.torn.com";
        },
    });
}

function resolveTokenCallback(response) {
    // TODO: Implement error handling in this
    let responseJSON = response.response;

    if (response.responseType === undefined) {
        responseJSON = JSON.parse(response.responseText);
        response.responseType = "json";
    }

    accessToken = responseJSON.access_token;
    accessTokenExpiration = Math.floor(Date.now() / 1000) + responseJSON.expires_in;
    const refreshToken = responseJSON.refresh_token ?? null;

    GM_setValue(`${GM_PREFIX}:access-token`, accessToken);
    GM_setValue(`${GM_PREFIX}:access-token-expires`, accessTokenExpiration);

    if (refreshToken == null) {
        // We want to delete the refresh token if none was provided from /oauth/token to
        // avoid falsely indicting that an access token can be refreshed.
        GM_deleteValue(`${GM_PREFIX}:refresh-token`);
    } else {
        GM_setValue(`${GM_PREFIX}:refresh-token`, refreshToken);
    }

    return;
}
