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
let accessRefreshToken = GM_getValue(`${GM_PREFIX}:refresh-token`, null);
export const redirectURI = `https://www.torn.com/tornium/${APP_ID}/oauth/callback`;
const REFRESH_TOKEN_HASH_ALGORITHM = "SHA-256";
const REFRESH_TOKEN_LOCAL_STORAGE_KEY = `${GM_PREFIX}:refresh-token-hash`;

// We will use a broadcast channel here as this appears to be more reliable than 
// using a `GM_addValueChangeListener` on each key, especially as that GM feature is
// not supported on all platforms (such as TornPDA).
const tokenBroadcastChannel = new BroadcastChannel(`${GM_PREFIX}:access-token-updates`);
tokenBroadcastChannel.onmessage = (event) => {
    accessToken = event.data.accessToken;
    accessTokenExpiration = event.data.accessTokenExpiration;
    accessRefreshToken = event.data.accessRefreshToken;
    updateRefreshTokenHash();

    log("Updated access token from another tab via broadcast channel...");
};

export function isAuthExpired() {
    // Let us refresh the access token and its expiration to ensure we're using "fresh" values.
    accessToken = GM_getValue(`${GM_PREFIX}:access-token`, null);
    accessTokenExpiration = GM_getValue(`${GM_PREFIX}:access-token-expires`, 0);

    if (accessToken == null || accessTokenExpiration == 0) {
        // Access token not set
        return true;
    } else if (Math.floor(Date.now() / 1000) >= accessTokenExpiration) {
        return true;
    }

    return false;
}

export function hasRefreshToken() {
    // Let us refresh the refresh token to ensure we're using "fresh" values.
    accessRefreshToken = GM_getValue(`${GM_PREFIX}:refresh-token`, null);

    return accessRefreshToken != null;
}

export async function refreshToken(forceRefresh = false) {
    const acquiredLock = await navigator.locks.request(
        `${GM_PREFIX}:refresh-token-lock`,
        { mode: "exclusive", ifAvailable: true },
        async (lock) => {
            if (lock == null) {
                // With ifAvailable = true, if the lock request is already held and cannot be
                // granted, null will be returned instead of a lock.
                log("Failed to achieve lock. Skipping...");
                return false;
            }

            // Re-check state inside the lock!
            if (!isAuthExpired() && !forceRefresh) {
                log("Token was successfully refreshed by another tab. Aborting request.");
                return true;
            } else if (!hasRefreshToken()) {
                log("There is no longer a refresh token to use. Aborting request.");
                return true;
            } else if (!(await hasValidRefreshTokenHash())) {
                // The hash of the refresh token from the userscript manager's storage doesn't
                // match the hash stored in local storage. This likely indicates that the
                // refresh token has been updated by some other tab and this tab is holding
                // an old value. We shouldn't delete the refresh token in case it's valid.
                log("There is a mismatch in the refresh token hash and the hash stored in local storage. Aborting request.");
                return true;
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
        await navigator.locks.request(`${GM_PREFIX}:refresh-token-lock`, async (lock) => {});
        log("Lock released by the other tab.");

        // accessToken = GM_getValue(`${GM_PREFIX}:access-token`, null);
        // accessTokenExpiration = GM_getValue(`${GM_PREFIX}:access-token-expires`, 0);
    }
}

async function doRefreshToken() {
    if (!hasRefreshToken()) {
        return;
    }

    log("Attempting to refresh access token with the refresh token...");

    // We want to immediately delete the refresh token to ensure it's not reused as to
    // avoid triggering the code for multiple usages of a refresh token.
    GM_deleteValue(`${GM_PREFIX}:refresh-token`);

    const tokenData = new URLSearchParams();
    tokenData.set("grant_type", "refresh_token");
    tokenData.set("refresh_token", accessRefreshToken);
    tokenData.set("scope", APP_SCOPE);
    tokenData.set("client_id", APP_ID);

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
        try {
            responseJSON = JSON.parse(response.responseText);
            response.responseType = "json";
        } catch (error) {
            log("Failed to parse token response: " + error);
            return;
        }
    }

    if (response.status !== 200 || responseJSON.error) {
        log(`Failed to update access token with an OAuth error: ${responseJSON.error || response.statusText}`);

        // If the server explicitly rejected the grant (e.g. family revoked)
        // purge the tokens to force a fresh login.
        if (responseJSON.error === "invalid_grant") {
            GM_deleteValue(`${GM_PREFIX}:access-token`);
            GM_deleteValue(`${GM_PREFIX}:access-token-expires`);
            GM_deleteValue(`${GM_PREFIX}:refresh-token`);
            localStorage.removeItem(REFRESH_TOKEN_LOCAL_STORAGE_KEY);

            accessToken = null;
            accessTokenExpiration = 0;
            accessRefreshToken = null;

            tokenBroadcastChannel.postMessage({
                accessToken: accessToken,
                accessTokenExpiration: accessTokenExpiration,
                accessRefreshToken: accessRefreshToken,
            });
        }
        return;
    }

    accessToken = responseJSON.access_token;
    accessTokenExpiration = Math.floor(Date.now() / 1000) + responseJSON.expires_in;
    accessRefreshToken = responseJSON.refresh_token ?? null;

    GM_setValue(`${GM_PREFIX}:access-token`, accessToken);
    GM_setValue(`${GM_PREFIX}:access-token-expires`, accessTokenExpiration);

    if (accessRefreshToken == null) {
        // We want to delete the refresh token if none was provided from /oauth/token to
        // avoid falsely indicting that an access token can be refreshed.
        GM_deleteValue(`${GM_PREFIX}:refresh-token`);
        localStorage.removeItem(REFRESH_TOKEN_LOCAL_STORAGE_KEY);
    } else {
        GM_setValue(`${GM_PREFIX}:refresh-token`, accessRefreshToken);
        updateRefreshTokenHash();
    }

    tokenBroadcastChannel.postMessage({
        accessToken: accessToken,
        accessTokenExpiration: accessTokenExpiration,
        accessRefreshToken: accessRefreshToken,
    });

    return;
}

async function getRefreshTokenHash() {
    if (accessRefreshToken == null) {
        return null;
    }

    const encoder = new TextEncoder();
    const encodedRefreshToken = encoder.encode(accessRefreshToken);
    const hashedRefreshToken = await window.crypto.subtle.digest(REFRESH_TOKEN_HASH_ALGORITHM, encodedRefreshToken);
    const hashedRefreshTokenHex = new Uint8Array(hashedRefreshToken).toHex();
    return hashedRefreshTokenHex;
}

async function updateRefreshTokenHash() {
    if (window.location.host != "www.torn.com") {
        // Setting the refresh token hash on the Tornium page is useless as it can't be
        // accessed by the script normally.
        return;
    }

    const hashedRefreshToken = await getRefreshTokenHash();
    localStorage.setItem(REFRESH_TOKEN_LOCAL_STORAGE_KEY, hashedRefreshToken);
}

async function hasValidRefreshTokenHash() {
    // We want to check if the hash of the refresh token found in the local storage
    // matches the hash of the refresh token found in the userscript's data store. If
    // they are not the same, this indiciates that the userscript is returning cached
    // values of the refresh token which are not necessarily accurate. If there is a
    // mismatch between the values, we should remove the refresh token so that the
    // user is forced to re-authenticate.
    accessRefreshToken = GM_getValue(`${GM_PREFIX}:refresh-token`, null);

    if (accessRefreshToken == null) {
        return false;
    }

    const refreshTokenHash = await getRefreshTokenHash();
    const refreshTokenLocalStorageHash = localStorage.getItem(REFRESH_TOKEN_LOCAL_STORAGE_KEY);

    if (refreshTokenLocalStorageHash == null) {
        // If there is no token hash stored in local storage, we should set it to ensure
        // other tabs have a value when checking the validity of their refresh token
        // value.
        // localStorage.setItem(REFRESH_TOKEN_LOCAL_STORAGE_KEY, refreshTokenHash);
        // return true;
    }

    return refreshTokenHash === refreshTokenLocalStorageHash;
}
