# Data Use and Storage Policy
This document supplements Tornium's [Privacy Policy](https://tornium.com/privacy) to provide more details regarding Tornium's storage and use of user data. 
Tornium offers toggles on the [user settings](https://tornium.com/settings) page for you to enable/disable the usage of your API key for certain features. You can toggle the following usage of your API key:
- [Share CPR](#user-cpr): When enabled, this will collect the CPR of OCs in recruiting status (even if you're not in them) with your API key and share those CPRs with members of your faction.
- [Share opponent stats](#user-attacks): When enabled, this will collect the stat scores of users you attack with your API key and of users who attack you and share those stat scores with either all Tornium users or members of your faction through the [stat database](https://tornium.com/stats/db).
- [Share overdosed drug](#user-logs): When enabled, this will collect the drug you overdosed upon from your user logs and share that data with your faction.
- [Share public data](#general-torn-data): When enabled, this will collect public data on other Torn users, factions, stocks, etc. and share that data with all users of Tornium.

If you have any questions or concerns regarding how Tornium stores your data, please create a ticket in Tornium's support server. If you would like your data in Tornium to be deleted, send an in-game mail to [tiksan [2383326]](https://www.torn.com/profiles.php?XID=2383326).

## API Keys
We persistently store Torn API keys to retrieve data from Torn regarding your user and potentially your faction, company, and other data depending on features enabled and permissions granted to you in-game. Your API key(s) will only be used for features regarding your account, regarding your faction if you have the API Access permission, regarding any Discord servers in which you are an admin. No other user will be able to see your API key(s).

## User Attacks
We collect user attacks to calculate the stat scores of the opponent for the stat database. This data (except for related data in the stat database) is not stored persistently. Your attacks cannot be accessed by anyone. This feature for your account can be disabled to not use your API key in Tornium's [user settings](https://tornium.com/settings) under `Share opponent stats`.

## User Battle Stats
We collect the battle stats of users who are signed into Tornium and potentially their faction members through <a href="https://www.tornstats.com">TornStats</a> to calculate stat scores from attacks and to calculate estimated respect for the chain list generator and stat database. All users' battle stats are NOT shared publicly with anyone nor do we view them. This data is stored persistently.

## User CPR
We collect the Organized Crime 2.0 success chance of users for each OC position for each OC type if the user's faction has migrated to Organized Crimes 2.0. This data can be accessed by your faction's members with the "Manage Organized Crimes" permission. This feature for your account can be disabled in Tornium's [user settings](https://tornium.com/settings) under `Share CPR`.

## User Logs
If you have a full access API key on Tornium, we may collect your user logs for the following log categories and reasons:

**(category) Item use drug**: This data is used for overdose drug detection. The data on the drug overdosed on can be accessed by your faction's members with faction API access. This feature for your account can be disabled in Tornium's [user settings](https://tornium.com/settings) under `Share overdosed drug`.

## Faction Attacks
We may collect your faction attacks for potential retaliations, for the chain timer, for updating the stat database. This data (except for related data in the stat database) is not stored persistently. Your faction attacks cannot be accessed by anyone.

## Faction Crimes
We collect your faction organized crimes for related notifications (e.g. when an organized crime is delayed). This data is stored persistently and can be accessed by any member of your faction with the "Manage Organized Crimes" permission.

## Faction Armory
We collect your faction armory data for notifications when the armory is low on stock for specific item(s), for overdose drug detection, and for armory usage reporting. This data is stored persistently and can be accessed by any member of your faction with faction API access permissions.

## Faction Funds
We collect your faction funds data to handle withdrawal requests for members against the faction's vault. This data (except for related data in withdrawal requests) is not stored persistently. Your faction funds cannot be accessed by anyone.

## Faction Positions
We collect your faction positions to handle permissions on Tornium and to determine which faction members can access data through the API. This data is stored persistently. Your faction positions can not be directly accessed by anyone with the exception of members viewing which members have faction API access and banking permissions.

## Faction Overdoses
We collect your faction overdoses for overdose notifications. This data is stored persistently. Your faction overdoses cannot be accessed by anyone, but notifications for faction overdoses may be sent to the linked Discord server.

## General Geolocation
We log the full IP addresses used to log in to accounts and retain that data for account security. This data is stored persistently. We also log IP addresses for all requests on a rolling basis for monitoring purposes. This data can only be accessed by Tornium administartor(s).

## General Torn Data
We collect general, public Torn data (such as all items) to keep our database up-to-date using the API keys who have toggled `Share public data` in Tornium's [user settings](https://tornium.com/settings). This data is stored on a persistent basis. This data can be accessed any user. Using your API key to collect this data can be disabled in Tornium's [user settings](https://tornium.com/settings) under `Share public data`.
