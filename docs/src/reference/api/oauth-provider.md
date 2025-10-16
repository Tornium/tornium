# OAuth Provider
Tornium includes an OAuth provider following [RFC 6479](https://datatracker.ietf.org/doc/html/rfc6749) to allow users to securely interact with Tornium's API. This document outlines supported flows, client registration, and general security considerations.

## Supported Flows
Tornium supports the following [OAuth flows](https://datatracker.ietf.org/doc/html/rfc6749#section-1.2):
- [Authorization Code Grant](#authorization-code-grant)
- Device Authorization Grant (coming soon)
- [Refresh Token Grant](#refresh-token-grant)

### Authorization Code Grant
### Refresh Token Grant

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

## Security Considerations
- PKCE ([RFC 7635](https://datatracker.ietf.org/doc/html/rfc7636)) is **REQUIRED** for all public clients.
- All redirect URIs **MUST** use HTTPS.
