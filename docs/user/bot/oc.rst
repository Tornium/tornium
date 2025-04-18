.. _oc:

Organized Crimes
================
This is a collection of features for **Organized Crimes** (OCs). This collection of features would be set up on the bot's dashboard for a server under the OC sub-page.

.. note::
   Tornium only supports OCs 2.0 now; admins of Discord servers containing legacy OCs 1.0 factions can create a ticket on the Discord support server to modify their OC-related configuration on their Discord server. However, OCs 1.0 support is to be considered deprecated and will be removed in the future (at a currently unknown date).

Delayed OCs
```````````
When an organized crime is delayed (e.g. by a member in the OC flying, being in the hospital, etc.), a notification will be sent in the specified channel. An optional set of OC names to trigger upon can also be specified to act as a whitelist such that only whitelisted crimes will be triggered.

OCs Missing Tools
`````````````````
When an organized crime is missing a required tool or material, a notification will be sent in the specified channel. An optional set of OC names to trigger upon can also be specified to act as a whitelist such that only whitelisted crimes will be triggered.

Extra-Range OCs
```````````````
Extra-range OC notifications will alert in the specified channel when an organized crime slot has a **Checkpoint Pass Rate** (CPR) outside of the specified range. The global CPR range is the default range applied to all OCs except for OCs with a specific range. Each named OC (e.g. "Break the Bank") can have a local CPR range that overrides the default global range.
