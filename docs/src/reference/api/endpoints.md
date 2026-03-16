# Endpoints
The Tornium API supports the following resource APIs:
- [Faction API](#faction-api)
- [Stat API](#stat-api)
- [Stocks API](#stocks-api)
- [Users API](#users-api)

All API endpoints require [OAuth authentication and authorization](./oauth-provider.md) against a registered application before performing any API calls.

All API endpoints share a 250 per minute global ratelimit, however this ratelimit can change without notice. Therefore, clients **SHOULD** rely upon ratelimiting headers to determine calls remaining and the ratelimit expiration. The ratelimiting will use the following headers:
- `X-RateLimit-Limit`: Maximum number of API calls until the ratelimit expires
- `X-RateLimit-Remaining`: Number of API calls remaining until the ratelimit expires
- `X-RateLimit-Reset`: Seconds until the ratelimit expires

**WARNING:** API endpoints are subject to change, potentially without notice.

## API Errors
All API errors will be of the format:
```json
{
    "code": <integer>,
    "name": <string>,
    "message": <string>,
    "details?": <object>
}
```

If more information is available beyond the base API error, the `details` field will be populated (typically under `details.message`). A list of valid API errors can be found in the [source code](https://github.com/Tornium/tornium/blob/master/application/controllers/api/v1/utils.py#L23).

## Faction API
### Get Faction Retaliations
Get all known, potential retaliations for the user's faction.

**Scopes Required:** `faction:attacks` (or `faction`)

```http
GET /api/v1/faction/<int:faction_id>/attacks/retaliations HTTP/1.1
Authorization: Bearer {{ access_token }}

[
    {
        "code": "bd80bb9c505a97ce7d66ddeee9433cf0",
        "attack_ended": 1761708665,
        "defender: {
            "ID": 2383326,
            "name": "tiksan"
        },
        "attacker": {
            "ID": 1,
            "name": "Chedburn"
        }
    }
]
```

### Get Faction Member Balance
Get the balance of the authenticated user in the vault of the user's faction.

**Scopes Required:** `faction:banking` (or `faction`) and `torn_key:usage`

```http
GET /api/v1/faction/banking/vault HTTP/1.1
Authorization: Bearer {{ access_token }}

{
    "player_id": 2383326,
    "faction_id": 15644,
    "money_balance": 123456,
    "points_balance": 123
}
```

### Create Faction Vault Request
Create a vault request against the authenticated user's faction. This requires the faction to be linked to a Discord server and to have banking set up on that Discord server.

The `amount` parameter supports the same values as the [slash command](../bot-banking.md#withdraw-command) including values such as `"all"`, `"1m"`, and `1000000`. If the `timeout` parameter is `null`, the request will never time out.

The `guid` in the vault request response can be used to create a fulfillment link of the form:
```
https://tornium.com/faction/banking/fulfill/<guid>
```

**Scopes Required:** `faction:banking` (or `faction`)

```http
POST /api/v1/faction/<int:faction_id>/banking HTTP/1.1
Authorization: Bearer {{ access_token }}
Content-Type: application/json

{
    "amount": "all",
    "type": "money_balance",
    "timeout": 1761708665
}

{
    "id": 1234,
    "guid": "dc79b83b-2ece-4ce9-9324-59464e89baaa",
    "user_id": 2383326,
    "faction_id": 15644,
    "amount": 12345678,
    "type": "money_balance",
    "expires_at": 1761708665
}
```

**Body Parameters**

| Field     | Type                      | Description                                          | Default   | Required |
| --------- | ------------------------- | ---------------------------------------------------- | --------- | -------- |
| `amount`  | Integer or String         | Amount to withdraw                                   |           | True     |
| `type`    | String                    | Type of request: `money_balance` or `points_balance` |           | True     |
| `timeout` | Unix Timestamp or null    | Earliest expiration timestamp                        | Never     | False    |


### Cancel Faction Vault Request
Cancel a vault request against the authenticated user's faction. If the user has banking permissions, the user can cancel any faction members' vault request. If the use does not have banking permissions, they can only cancel their own vault requests.

The `request_id` path parameter can either be the `wid` of the request or the `guid` of the request. This API endpoint return HTTP 204 with no response body if the request has been successfully cancelled.

**Scopes Required:** `faction:banking` (or `faction`)

```http
DELETE /api/v1/faction/<int:faction_id>/banking/<request_id> HTTP/1.1
Authorization: Bearer {{ access_token }}
```

### List Vault Requests
List all applicable vault requests against the authenticated user's faction.

If the `search_type` is `pending`, this endpoint will return all requests that have not been fulfilled or cancelled; otherwise, the endpoint will return all requests. If the `scope` is `faction` and the user has banking permisions, this endpoint will return either the pending or all requests for all faction members; otherwise, if the `scope` is `user`, the endpoint will return the pending or all requests for the authenticated user.

**Scopes Required:** `faction:banking` (or `faction`)

```http
GET /api/v1/faction/<int:faction_id>/banking HTTP/1.1
Authorization: Bearer {{ access_token }}
```

**Query Parameters**

| Field          | Type             | Description                            | Default   | Required |
| -------------- | ---------------- | -------------------------------------- | --------- | -------- |
| `search_type`  | String           | Type of request: `pending` or `all`    | `pending` | False    |
| `scope`        | String           | Scope of requests: `user` or `faction` | `user`    | False    |
| `limit`        | Integer          | Response limit (1-100)                 | 100       | False    |
| `before`       | UNIX timestamp   | Latest timestamp to return             |           | False    |

### Get Organized Crimes Names
Get a list of names of all organized crimes. The data from this API endpoint is cached for an hour.


```http
GET /api/v1/faction/crime/names HTTP/1.1
Authorization: Bearer {{ access_token }}

[
    "Break the Bank",
    "Market Forces",
    "Clinical Precision"
]
```

### Get Organized Crime Delays
Get a list of members of the authenticated user's faction who have delayed organized crimes.

**Scopes Required:** `faction:crimes` (or `faction`)

```http
GET /api/v1/faction/<int:faction_id>/crime/delays HTTP/1.1
Authorization: Bearer {{ access_token }}
Content-Type: application/json

{
    "limit": 50
}

[
    {
        "oc_id": 1234,
        "user_id": 2383326,
        "oc_position": "Muscle",
        "oc_position_index": 3,
        "delay_reason": "Flying to Mexico"
    }
]
```

**Query String Parameters**

| Field    | Type    | Description                  | Default | Required |
| -------- | ------- | ---------------------------- | ------- | -------- |
| `before` | Integer | Minimum OC ID for pagination |         | False    |
| `after`  | Integer | Maximum OC ID for pagination |         | False    |
| `limit`  | Integer | Maximum number of delays     | 100     | False    |


### Get Faction Members
Get a list of members of a specific faction.

**Scopes Required:** none

```http
GET /api/v1/<int:faction_id>/members HTTP/1.1
Authorization: Bearer {{ access_token }}

[
    {
        "ID": 2383326,
        "name": "tiksan",
        "level": 100,
        "discord_id": 695828257949352028
    }
]
```

### [DEPRECATED] Get Faction Positions
Get a mapping of faction positions for the authenticated user's faction.

**Scopes Required:** `faction`

```http
GET /api/v1/faction/positions HTTP/1.1
Authorization: Bearer {{ access_token }}

{
    "positions": [
        {
            "_id": "2da1bfe9-d654-43a2-9733-ef76bfb6e500",
            "name": "Crusader",
            "faction_tid": 15644,
            "default": True,
            "use_medical_item: False,
            "use_booster_item: False,
            "use_drug_item: False,
            "use_energy_refill: False,
            "use_nerve_refill: False,
            "loan_temporary_item: False,
            "loan_weapon_armory: False,
            "retrieve_loaned_armory: False,
            "plan_init_oc: False,
            "access_fac_api: False,
            "give_item: False,
            "give_money: False,
            "give_points: False,
            "manage_forums: False,
            "manage_applications: False,
            "kick_members: False,
            "adjust_balances: False,
            "manage_wars: False,
            "manage_upgrades: False,
            "send_newsletters: False,
            "change_announcement: False,
            "change_description: False
        }
    ]
}
```

## Stat API
### Generate Chain List
Generate a chain list for the authenticated user. The authenticated user must have a stat score in the database, either from being logged into Tornium with an API key or through the faction's TornStats.

This API endpoint has an additional ratelimit currently set to 5 per minute.

**Scopes Required:** none

```http
POST /api/v1/stat/chain-list HTTP/1.1
Authorization: Bearer {{ access_token }}
Content-Type: application/json

{
    "minimum_difficulty": 1,
    "maximum_difficulty": 3,
    "minimum_level": 1,
    "maximum_level": 100,
    "sort_order": "respect",
    "limit": 100,
    "is_factionless": True,
    "is_inactive": True
}

[
    {
        "time_added": 1761708665,
        "stat_score": 1234,
        "fair_fight": 1.23,
        "respect": 2.19,
        "target": {
            "ID": 2383326,
            "name": "tiksan",
            "faction": {
                "ID": 15644,
                "name": "New Sith Order"
            },
            "last_action": 1761708665,
            "last_refresh": 1761708665
        }
    }
]
```

**JSON Parameters**

| Field                | Type       | Description                                           | Default | Required |
| -------------------- | ---------- | ----------------------------------------------------- | ------- | -------- |
| `minimum_difficulty` | Number     | Minimum fair fight the target would provide           | 1 | False    |
| `maximum_difficulty` | Number     | Maximum fair fight the target would provide           | 3 | False |
| `minimum_level`      | Integer    | Minimum level the target has                          | 1 | False |
| `maximum_level`      | Integer    | Maximum level the target has                          | 100 | False |
| `sort_order`         | String     | Sort order of the targets (`random`, `recently-updated`, `highest-respect`) | `random` | False |
| `limit`              | Integer    | Maximum number of targets to list                     | 25 | False |
| `is_factionless`     | Boolean    | Flag to only include targets that are not in factions | False | False |
| `is_inactive`        | Boolean    | Flag to only include targets that are not active | False | False |


## Stocks API
### Get Stocks Data
Get the data on all stocks for the last known tick. Returns a map of stock IDs and stock data.

**Scopes Required:** none

```http
GET /api/v1/stocks HTTP/1.1
Authorization: Bearer {{ access_token }}

{
    "1": {
        "timestamp": 1761708665,
        "price": 787.59,
        "market_cap": 14250000000,
        "shares": 12374372,
        "investors": 134,
        "acronym": "MCS"
    }
}
```

### Get Stock Benefits Data
Get the list of benefits for each stock.

**Scopes Required:** none

### Get stock Movers Data
Get the lists of gainers and losers over the periods:
- d1 (24 hours)
- d7 (7 days)
- m1 (30 days)

**Scopes Required:** none

## Users API
### Get User
Get the information on the authenticated user.

**Scopes Required**: `identity`

```http
GET /api/v1/user HTTP/1.1
Authorization: Bearer {{ access_token }}

{
    "tid": 2383326,
    "name": "tiksan",
    "username": "tiksan [2383326]",
    "last_refresh": 1761708665,
    "discord_id": 695828257949352028,
    "factiontid": 15644,
    "last_action": 1761708665
}
```

### Get Specific User
Get the information on specific Torn user.

**Scopes Required:** none

If the target user is to be updated, the `torn_key:usage` scope must be included.

```http
GET /api/v1/user/<int:user_id> HTTP/1.1
Authorization: Bearer {{ access_token }}

{
    "tid": 2383326,
    "name": "tiksan"
    "username": "tiksan [2383326]",
    "level": 100,
    "last_refresh": 1761708665,
    "discord_id": 695828257949352028,
    "faction": {
        "tid": 15644,
        "name": "New Sith Order"
    },
    "last_action": 1761708665
}
```

**Query String Parameters**

| Field   | Type    | Description                                     | Default | Required |
| ------- | ------- | ----------------------------------------------- | ------- | -------- |
| `refresh` | Boolean | If the target user's data should be refreshed | False   | False    |


### Get User Stats Estimate
Get the stat estimate of a specific user through Tornium's stat estimation model.

**Scopes Required:** none

If the user has an API key and the `torn_key:usage` scope is included, the target user's data may be updated if the target user's personal stats were last updated more than a one week previously.

```http
GET /api/v1/user/estimate/<int:user_id> HTTP/1.1
Authorization: Bearer {{ access_token }}

{
    "stat_score": 1234,
    "min_bs": 380689,
    "max_bs": 553729,
    "expiration": 1761708665
}
```

### Get User Historical Stats
Get the latest historical stats of a specific user through Tornium's [stat database](https://tornium.com/stats/db).

**Scopes Required:** None

```http
GET /api/v1/user/<int:user_id>/stat HTTP/1.1
Authorization: Bearer {{ access_token }}

{
    "stat_score": 1234,
    "min": 380689,
    "max": 553729,
    "timestamp": 1761708665
}
```
