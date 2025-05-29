# Bot Organized Crimes
Tornium supports notifications for organized crime-related events:
- [OCs missing tools](#missing-tools-ocs)
- [OCs delayed](#delayed-ocs)
- [OCs extra range](#extra-range-ocs)

Tornium updates and performs all checks for the latest organized crimes every five minutes. All features can be configured to send messages in specific channels and ping roles. Additionally, all features can be optionally configured to only check against specific OC names (e.g. `Honey Trap`).

***WARNING:*** This series of features is in active development and will change as time passes.
***DEPRECATION NOTICE:*** Factions remaining on OCs 1.0 are deprecated and will no longer be supported on August 1st.

These configuration options can be set on the Tornium website on the organized crimes dashboard for any Discord server the Tornium bot is in. For basic information on setting up OCs in a Discord server, the [tutorial](../tutorial/discord-server-oc.md) is recommended.

## Missing Tools OCs
When configured, Tornium will alert when an organized crime has a member missing a required tool or material. This will only be alerted upon 24 hours before an organized crime would be ready.

## Delayed OCs
When configured, Tornium will alert when an organized crime has been delayed by a member not being available (e.g. in the hospital or flying) when the organized crime is ready.

## Extra Range OCs
When configured, Tornium will alert when an organized crime has a member whose CPR is outside the configured bounds for that organized crime. The global minimum-maximum will be used when a per-OC minimum-maximum pair is not set.

- **Global Minimum**: The default minimum CPR for all OCs
- **Global Maximum**: The default maximum CPR for all OCs
- **Per-OC Minimum**: The minimum CPR for all OCs with that name
- **Per-OC Maximum**: The maximum CPR for all OCs with that name
