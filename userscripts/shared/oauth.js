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

export function isAuthExpired() {
    if (accessToken == null || accessTokenExpiration == 0) {
        // Access token not set
        return true;
    } else if (Math.floor(Date.now() / 1000) >= accessTokenExpiration) {
        return true;
    }

    return false;
}

export function hasRefreshToken() {
    return GM_getValue(`${GM_PREFIX}:refresh-token`) != null;
}

export function refreshToken() {
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
            log("Access token successfully refreshed");
            // TODO: Implement successful message
        },
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
