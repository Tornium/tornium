# How to give an application access to your faction?
This guide shows you how to grant and revoke consent for an application (such as a Discord bot or a faction tool) to access your faction's data on Tornium without a user having to manually authorize it. Only the faction's leader or co-leader can grant or revoke consent.

## Granting Consent
1) Get the consent link from the application's developer. The link will be of form `https://tornium.com/oauth/{{ client_id }}/consent` followed by the faction ID and the permissions requested.
2) Open the link while signed into Tornium.
3) Review the requested permissions. You can untick any permissions you don't want to give the application.
4) Click "Consent".

The application will now be able to access your faction's data for the permissions you approved until consent is revoked. Ensure that you trust the application before granting consent, as it may be able to access sensitive information about your faction such as armory usage, retaliations, and organized crimes.

If you open the consent link again and approve a different set of permissions, the previous consent will be replaced and the application will have to request access again.

## Revoking Consent
The leader or coleader of the faction can revoke the application's consent to immediately force the application to lose access to the faction's data at any time and the application.
1) Visit the [Consents](https://tornium.com/faction/consent) page of the faction dashboard.
2) Find the application in the list of consents.
3) Click "Revoke Consent".

For more in-depth details on how applications use consent, see the [OAuth provider reference](../reference/api/oauth-provider.md#client-credentials-grant).
