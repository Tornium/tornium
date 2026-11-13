# OAuth Provider
Tornium includes an OAuth provider following [RFC 6749](https://datatracker.ietf.org/doc/html/rfc6749) to allow users to securely interact with Tornium's API. This document outlines supported flows, client registration, and general security considerations.

## Supported Flows
Tornium supports the following [OAuth flows](https://datatracker.ietf.org/doc/html/rfc6749#section-1.2):
- [Authorization Code Grant](#authorization-code-grant)
- [Client Credentials Grant](#client-credentials-grant)
- [Refresh Token Grant](#refresh-token-grant)

### Authorization Code Grant
Authorization code grant is the typical OAuth2 flow with an authorization code exchanged for the user's access token. This reference will NOT describe all the intricacies of OAuth2; it is suggested that you read all related RFCs.

For OAuth requests, a private client **MUST** use the `client_secret_basic` client authentication method in a POST request with the following format:
```
Authorization: Basic {{ Base64(<client_id>:<client_secret>) }}
```

Additionally, a public client **MUST** use the `none` client authentication method and **MUST** use Proof Key for Code Exchange (PKCE).

#### Client Authorization
The client **MUST** redirect the user to Tornium's authorization URL to authorize the application for their user for the requested scopes. Upon acceptance by the user, Tornium will redirect the user to the client through the included `redirect_uri`. The authorization code will be provided as the query parameter `code`. The authorization redirect URI to Tornium **MUST** be of form:

```uri
https://tornium.com/oauth/authorize?response_type=code&client_id={{ client_id }}&state={{ state }}&scope={{ scope }}&code_challenge_method=S256&code_challenge={{ code_challenge }}&redirect_uri={{ redirect_uri }}
```

#### Redirect URI
Upon successful authorization by the user and redirection to the `redirect_uri`, the `code` as a query parameter in the redirect **MUST** be exchanged for the user's access token with a `POST` request to the token URL:

```http
POST /oauth/token HTTP/1.1
Host: tornium.com
Content-Type: application/x-www-form-urlencoded
Authorization: Basic {{ base64_client_secret }}

code={{ code }}&grant_type=authorization_code&scope={{ scope }}&client_id={{ client_id }}&code_verifier={{ code_verifier }}&redirect_uri={{ redirect_uri }}

HTTP/1.1 200 OK
Content-Type: application/json
Cache-Control: no-store
Pragma: no-cache

{
    "access_token": "{{ access_token }}",
    "token_type": "Bearer",
    "expires_in": {{ expires_in }},
    "refresh_token": "{{ refresh_token }}"
}
```

### Client Credentials Grant
Client credentials grant is the OAuth2 flow intended for machine-to-machine authentication, for applications such as cronjobs and other backend tooling, allowing a client to obtain an access token without the manual intervention of a user. Therefore, the access tokens provided by this grant are associated with the OAuth client instead of a user unlike authorization code grant resulting in two types of access tokens:
- Generic access tokens: Access tokens not bound to any resource and can only access API endpoints providing generic data not associated to any resource.
- Resource access tokens: Access tokens bound to a single, specific resource (such as a faction) granted consent by a user with sufficient permissions to the resource. This access token will only be able to access the scopes when thatuser granted consent.

This reference will primarily describe the specifics of Tornium's implementation of client credentials grant; therefore, it is suggested that you read all related RFCs for the specifics of how client credentials grant works.

For OAuth requests, the client **MUST** use the `client_secret_basic` client authentication method in a POST request with the following format:
```
Authorization: Basic {{ Base64(<client_id>:<client_secret>) }}
```

As the client secret for the OAuth client is the only credential requried to obtain access tokens, client credentials grant **MUST NOT** be used by applications that are unable to securely store secrets (such as userscripts).

#### Resource Consent
Before an application can obtain an access token for an OAuth client against a resource, a user with sufficient permissions of the resource **MUST** grant consent to the OAuth client to access the resource. Consent is granted to the OAuth client instead of the individual access tokens to allow for the client to obtain new access tokens for the resource until the consent is revoked.

To request consent, the application **SHOULD** direct a user with sufficient permissions for the resource to Tornium's consent URL of form:
```uri
https://tornium.com/oauth/{{ client_id }}/consent?resource={{ resource }}&scope={{ scope }}
```
where `resource` is the resource requesting consent from, of format `{{ resource_type }}:{{ resource_id }}` (instead of the absolute URI format as described by [RFC 8707](https://www.rfc-editor.org/rfc/rfc8707.html)), and the `scope` is the space-delimited list of scopes requested.

| Resource Type  | Format                     | Example                                   | Who can grant consent?  |
| -------------- | -------------------------- | ----------------------------------------- | ----------------------- |
| Faction        | `faction:{{ faction_id }}` | New Sith Order \[15644\]: `faction:15644` | Faction leader/coleader |
| Discord Server | `server:{{ guild_id }}`    | Tornium: `server:1132079436691415120`     | Server admin            |

The user granting consent can choose to only grant a subset of the scopes instead of all of the scopes requested. If consent is granted again for a resource that has already consented to the client:
- If the approved scopes are the same as the existing consent, nothing will change.
- If the approved scopes are different, the existing consent will be replaced. All access tokens issued under the previous consent will be revoked and the client MUST obtain new access tokens.

Once consent has been granted to a resource, the consent can be revoked at any time by anyone with sufficient permissions:
- Factions: The faction's leader or co-leader can revoke consent from the [Consents page](https://tornium.com/faction/consent) of the faction dashboard.
- Discord servers: An admin of the Discord server can revoke consent from the Consents page of the server's dashboard at https://tornium.com/bot/dashboard/{{ guild_id }}/consent.

By revoking the consent to the resource, the access tokens of the OAuth application issued under that resource consent will also be revoked and further requests will fail with `unauthorized_client` until consent is granted again.

#### Token Request
To obtain an access token, the resource parameter **MUST** be included in the same format as the consent URL and the requested scope **MUST** be a subset of the scopes the resource consented to.

```htp
POST /oauth/token HTTP/1.1
Host: tornium.com
Content-Type: application/x-www-form-urlencoded
Authorization: Basic {{ base64_client_secret }}

grant_type=client_credentials&resource={{ resource }}&scope={{ scope }}

HTTP/1.1 200 OK
Content-Type: application/json
Cache-Control: no-store
Pragma: no-cache

{
    "access_token": "{{ access_token }}",
    "token_type": "Bearer",
    "expires_in": 3600,
    "scope": "{{ scope }}"
}
```

To obtain a generic access token, the resource parameter **MUST** be omitted.

### Refresh Token Grant
When provided the refresh token from the original/previous token exchange, the refresh token grant will revoke the user's current access token for the client and grant a new access token (and a new refresh token if enabled) with an updated expiration. To utilize refresh token grant, the owner of the OAuth client must enable it which will result in refresh tokens being included in the token exchanges. Pursuant to [RFC 9700](https://www.rfc-editor.org/info/rfc9700/#section-4.14.2-5.2.1), all generated refresh tokens of a "family" (generated from the same series of refresh tokens) will be revoked if a refresh token is used more than once. This will also send a notification (as a Discord direct message) to the owner of the access token; it is **suggested** to indicate as such in your documentation/userscipt/etc. so that users will be aware of the circumstances resulting in that message.

**NOTE:** If refresh token grant is enabled then disabled, any access tokens generated with a refresh token will still be able to utilize refresh token grant. Further generated access tokens will not include a refresh token though.

```http
POST /oauth/token HTTP/1.1
Host: tornium.com
Content-Type: application/x-www-form-urlencoded
Authorization: Basic {{ base64_client_secret }}

grant_type=refresh_token&refresh_token={{ refresh_token }}

HTTP/1.1 200 OK
Content-Type: application/json
Cache-Control: no-store
Pragma: no-cache

{
    "access_token": "{{ access_token }}",
    "token_type": "Bearer",
    "expires_in": {{ expires_in }},
    "refresh_token": "{{ refresh_token }}"
}
```

## Client Registration
For an application to interact with Tornium's API, the application **MUST** be registered with the following information:
- Client Type: The type of application, which determines the OAuth flow used by the client:
    - Web App (Server-Side): authorization code grant with the `client_secret_basic` client authentication method
    - Userscript/SPA: authorization code grant with PKCE and the `none` client authentication method
    - Machine Application: client credentials grant with the `client_secret_basic` client authentication method
- Redirect URIs: List of whitelisted URLs for authorization code grant that **MUST** NOT contain wildcards.
- Scopes: List of scopes limiting data access of the application.
- Refresh Grant Usage: Toggle of whether the client will use refresh token grant.
- Client URI: URI of the homepage or main page of the application.
- Client ToS URI: URI of the terms of service of the application.
- Client Privacy Policy URI: URI of the privacy policy of the application.

The linked privacy policy **MUST** list/explain the following:
- The data retrieved from Tornium
- The usage of that data
- Retention of that data
- How that data can be deleted
- How and why that data is shared

The linked privacy policy **SHOULD** also include the following:
- A method to contact the application's developer regarding data concerns
- A description of how user data is protected by the application

**NOTE:** Tornium currently does not support Dynamic Client Registration ([RFC 7591](https://datatracker.ietf.org/doc/html/rfc7591)), so clients can only be registered through [Tornium's website](https://tornium.com/developers/clients).

### Scopes
This is a list of Tornium's OAuth2 scopes required for use of certain endpoints in the Tornium API. The documentation for individual API endpoints will state which scopes, if any, are required. By default, an application has access no scopes.

| Name            | Description                                                             |
| --------------- | ----------------------------------------------------------------------- |
| `identity`        | allows access to information on a user's identity                       |
| `faction`         | allows access to all information on the user's faction                  |
| `faction:armory`  | allows access to information related to the armory of a user's faction  |
| `faction:attacks` | allows access to information related to the attacks of a user's faction |
| `faction:banking` | allows access to the Tornium banking of a user's faction                |
| `faction:crimes`  | allows access to the organized crime information of the user's faction  |
| `torn_key:usage`  | allows the usage of the user's API key |


## Security Considerations
- To help prevent cross-site request forgery and clickjacking, the `state` parameter ([RFC 6749](https://datatracker.ietf.org/doc/html/rfc6749)) is **REQUIRED** for all clients. The `state` parameter will bind the user's authorization request to their authenticated state and **MUST** be sent in the authorization request and will be returned in the response. The client **MUST** validate the redirection by matching the redirected `state`; a mismatched `state` parameter may be the result of an intercepted request or failed authorization and its request **MUST** be denied.
- PKCE ([RFC 7636](https://datatracker.ietf.org/doc/html/rfc7636)) is **REQUIRED** for all public clients and is **RECOMMENDED** for all clients.
- All redirect URIs **MUST** use HTTPS.
- The client secret must be stored securely for confidential OAuth clients, otherwise it should only use the authorization code grant with `none` client authentication. If leaked, the client secret should immediately be regenerated.
- OAuth clients using client credentials grant **SHOULD** only request the scopes required by the application.

For more information, it is **RECOMMENDED** to read the relevant OAuth2 RFCs.
