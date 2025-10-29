# Endpoints
The Tornium API supports the following resource APIs:
- [Users API](#users-api)

All API endpoints require [OAuth authentication and authorization](./oauth-provider.md) against a registered application before performing any API calls.

## Users API
### User Resource
NYI

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

If the user is to be updated, the `torn_key:usage` scope must be included.

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

### Get User Stats Estimate
Get the stat estimate of a specific user through Tornium's stat estimation model.

### Get User Historical Stats
Get the historical stats of a specific user through Tornium's [stat database](https://tornium.com/stats/db).
