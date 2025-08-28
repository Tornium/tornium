export const accessToken = GM_getValue("tornium-retaliations:access-token", null);
export const accessTokenExpiration = GM_getValue("tornium-retaliations:access-token-expires", 0);

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
