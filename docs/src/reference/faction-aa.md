# Faction AA
Faction AA refers to the Faction `API Access` permission in-game. Members with faction positions granting this permission will have read-only access to faction data through the Torn API.

***WARNING:*** Members granted the AA permission will be able to access data through the API even if they don't have the permissions to access the data in-game. For example, a member with the AA permission who doesn't have banking permissions will not be able to see other members' vault balances in-game but can view them through the API.

Tornium utilizes the AA permission to grant faction members permission/access to modify certain faction-related features that aren't attached to Discord servers. Additionally, Tornium uses the API keys of members with the AA permission to retrieve faction data for features such as banking, retaliations, and others. As such, it is heavily discouraged to grant every member the AA permission.

A faction leader/co-leader can grant and revoke faction positions on the [faction positions page](https://www.torn.com/factions.php?step=your&type=1#/tab=controls&option=positions) under `Faction > Controls > Positions`. On the faction permissions page, the leader/co-leader will be able to change permissions for each position by pressing the cross or check marks to respectively enable or disable the selected permission for the specified faction position.
