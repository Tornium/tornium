# OAuth Provider
Tornium includes an OAuth provider following [RFC 6479](https://datatracker.ietf.org/doc/html/rfc6749) to allow users to securely interact with Tornium's API. This document outlines supported flows, client registration, and general security considerations.

## Supported Flows
Tornium supports the following [OAuth flows](https://datatracker.ietf.org/doc/html/rfc6749#section-1.2):
- [Authorization Code Grant](#authorization-code-grant)
- Device Authorization Grant (coming soon)
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

### Refresh Token Grant
To avoid indefinite impersonation of users on a public client (which are unable to properly secure a refresh token), only confidential clients may utilize the refresh token grant. The refresh token grant will revoke the user's current access token for the client and grant a new access token with an updated expiration.

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
- Redirect URIs: List of whitelisted URLs for authorization code grant that **MUST** NOT contain wildcards.
- Scopes: List of scopes limiting data access of the application.
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

**NOTE:** Tornium currently does not support Dynamic Client Registration ([RFC 7591](https://datatracker.ietf.org/doc/html/rfc7591)), so clients can only be registered through [Tornium](https://tornium.com/developers/clients).

### Scopes
This is a list of Tornium's OAuth2 scopes required for use of certain endpoints in the Tornium API. The documentation for individual API endpoints will state which scopes, if any, are required. By default, an application has access no scopes.

| Name            | Description                                                             |
| --------------- | ----------------------------------------------------------------------- |
| `identity`        | allows access to information on a user's identity                       |
| `faction`         | allows access to all infomration on the user's faction                  |
| `faction:attacks` | allows access to information related to the attacks of a user's faction |
| `faction:banking` | allows access to the Tornium banking of a user's faction                |
| `faction:crimes`  | allows access to the organized crime information of the user's faction  |
| `torn_key:usage`  | allows the usage of the user's API key |


## Security Considerations
- To help prevent cross-site request forgery and clickjacking, the `state` parameter ([RFC 6479](https://datatracker.ietf.org/doc/html/rfc6749)) is **REQUIRED** for all clients. The `state` parameter will bind the user's authorization request to their authenticated state and **MUST** be sent in the authorization request and will be returned in the response. The client **MUST** validate the redirection by matching the redirected `state`; a mismatched `state` parameter may be the result of an intercepted request or failed authorization and its request **MUST** be denied.
- PKCE ([RFC 7635](https://datatracker.ietf.org/doc/html/rfc7636)) is **REQUIRED** for all public clients and is **RECOMMENDED** for all clients.
- All redirect URIs **MUST** use HTTPS.

For more information, it is **RECOMMENDED** to read the relevant OAuth2 RFCs.
