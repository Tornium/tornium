import { APP_ID, APP_SCOPE, BASE_URL, clientLocalGM } from "./constants.js";

export const accessToken = GM_getValue("tornium-estimate:access-token", null);
export const accessTokenExpiration = GM_getValue("tornium-estimate:access-token-expires", 0);
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

    // TODO: Maybe check the API to determine if the access token is expired or revoked
    return false;
}

export function authStatus() {
    if (accessToken == null) {
        return "Disconnected";
    } else if (isAuthExpired()) {
        return "Expired";
    }

    // TODO: Maybe check the API to determine if the access token is expired or revoked
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
        onload: resolveTokenCallback,
    });
}

function resolveTokenCallback(response) {
    let responseJSON = response.response;

    if (response.responseType === undefined) {
        responseJSON = JSON.parse(response.responseText);
        response.responseType = "json";
    }

    const accessToken = responseJSON.access_token;
    const accessTokenExpiration = Math.floor(Date.now() / 1000) + responseJSON.expires_in;
    GM_setValue("tornium-estimate:access-token", accessToken);
    GM_setValue("tornium-estimate:access-token-expires", accessTokenExpiration);

    window.location.href = "https://torn.com";
    return;
}
