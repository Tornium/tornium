# Endpoints
The Tornium API supports the following resource APIs:
- [Stat API](#stat-api)
- [Stocks API](#stocks-api)
- [Users API](#users-api)

All API endpoints require [OAuth authentication and authorization](./oauth-provider.md) against a registered application before performing any API calls.

**WARNING:** API endpoints are subject to change, potentially without notice.

## Stat API
### Generate Chain List
Generate a chain list for the authenticated user. The authenticated user must have a stat score in the database, either from being logged into Tornium with an API key or through the faction's TornStats.

This API endpoint has an addition ratelimit currently set to 5 per minute.

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
    "last_refresh: 1761708665,
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
