# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import json
import random

from controllers.api.decorators import *
from models.faction import Faction
from models.servermodel import ServerModel
from models.user import User


@key_required
@ratelimit
@requires_scopes(scopes={"admin", "bot:admin"})
def verification_config(guildid, *args, **kwargs):
    client = redisdb.get_redis()
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    guild: ServerModel = ServerModel.objects(sid=guildid).first()

    if guild is None:
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "UnknownGuild",
                    "message": "Server failed to fulfill the request. The guild ID could not be matched with a server "
                    "in the database.",
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )

    return {
        "enabled": guild.config.get("verify"),
        "verify_template": guild.verify_template,
        "verified_roles": guild.verified_roles,
        "faction_verify": guild.faction_verify,
        "verify_log_channel": guild.verify_log_channel,
    }


@key_required
@ratelimit
@requires_scopes(scopes={"admin", "bot:admin"})
def guild_verification(*args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    client = redisdb.get_redis()
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    guildid = data.get("guildid")

    if guildid in ("", None, 0) or not guildid.isdigit():
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "GeneralError",
                    "message": "Server failed to fulfill the request. A valid guild ID and faction TID are required.",
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )

    guildid = int(guildid)
    guild: ServerModel = ServerModel.objects(sid=guildid).first()

    if guild is None:
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "UnknownGuild",
                    "message": "Server failed to fulfill the request. The guild ID could not be matched with a server "
                    "in the database.",
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )

    if request.method == "POST":
        if guild.config.get("verify") in (None, 0):
            guild.config["verify"] = 1
            guild.save()
        else:
            return (
                jsonify(
                    {
                        "code": 0,
                        "name": "GeneralError",
                        "message": "Server failed to fulfill the request. The guild's verification is already enabled.",
                    }
                ),
                400,
                {
                    "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
                    "X-RateLimit-Remaining": client.get(key),
                    "X-RateLimit-Reset": client.ttl(key),
                },
            )
    elif request.method == "DELETE":
        if guild.config.get("verify") in (None, 1):
            guild.config["verify"] = 0
            guild.save()
        else:
            return (
                jsonify(
                    {
                        "code": 0,
                        "name": "GeneralError",
                        "message": "Server failed to fulfill the request. The guild's verification is already disabled.",
                    }
                ),
                400,
                {
                    "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
                    "X-RateLimit-Remaining": client.get(key),
                    "X-RateLimit-Reset": client.ttl(key),
                },
            )
    else:
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "GeneralError",
                    "message": "Server failed to fulfill the request. An unknown caught HTTP method was passed.",
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )

    return (
        jsonify(
            {
                "verify": {
                    "enabled": guild.config.get("verify")
                    if guild.config.get("verify") is not None
                    else False,
                    "verify_log_channel": guild.verify_log_channel,
                    "faction_verify": guild.faction_verify,
                },
            }
        ),
        200,
        {
            "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
            "X-RateLimit-Remaining": client.get(key),
            "X-RateLimit-Reset": client.ttl(key),
        },
    )


@key_required
@ratelimit
@requires_scopes(scopes={"admin", "bot:admin"})
def guild_verification_log(*args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    client = redisdb.get_redis()
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    guildid = data.get("guildid")
    channelid = data.get("channel")

    if (
        guildid in ("", None, 0)
        or not guildid.isdigit()
        or channelid in ("", None, 0)
        or not channelid.isdigit()
    ):
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "GeneralError",
                    "message": "Server failed to fulfill the request. A valid guild ID and channel ID are required.",
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )

    guildid = int(guildid)
    channelid = int(channelid)
    guild: ServerModel = ServerModel.objects(sid=guildid).first()

    if guild is None:
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "UnknownGuild",
                    "message": "Server failed to fulfill the request. The guild ID could not be matched with a server "
                    "in the database.",
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )

    guild.verify_log_channel = channelid
    guild.save()

    return jsonify(
        {
            "verify": {
                "enabled": guild.config.get("verify")
                if guild.config.get("verify") is not None
                else False,
                "verify_log_channel": guild.verify_log_channel,
                "faction_verify": guild.faction_verify,
            },
        },
        200,
        {
            "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
            "X-RateLimit-Remaining": client.get(key),
            "X-RateLimit-Reset": client.ttl(key),
        },
    )


@key_required
@ratelimit
@requires_scopes(scopes={"admin", "bot:admin"})
def faction_verification(*args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    client = redisdb.get_redis()
    key = f'tornium:ratelimit:{kwargs["user"].tid}'

    guildid = data.get("guildid")
    factiontid = data.get("factiontid")

    if (
        guildid in ("", None, 0)
        or not guildid.isdigit()
        or factiontid in ("", None, 0)
        or not factiontid.isdigit()
    ):
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "GeneralError",
                    "message": "Server failed to fulfill the request. A valid guild ID and faction TID are required.",
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )

    guildid = int(guildid)
    factiontid = int(factiontid)
    guild: ServerModel = ServerModel.objects(sid=guildid).first()

    if guild is None:
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "UnknownGuild",
                    "message": "Server failed to fulfill the request. The guild ID could not be matched with a server "
                    "in the database.",
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )

    faction: Faction = Faction(factiontid, key=User(random.choice(guild.admins)).key)

    if request.method == "DELETE" and str(faction.tid) not in guild.faction_verify:
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "GeneralError",
                    "message": "Server failed to fulfill the request. Improper HTTP request type.",
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )

    if request.method == "DELETE" and data.get("remove") is True:
        del guild.faction_verify[str(factiontid)]
    else:
        if faction.tid not in guild.faction_verify:
            guild.faction_verify[str(factiontid)] = {"roles": [], "enabled": False}

        if request.method == "POST":
            guild.faction_verify[str(factiontid)]["enabled"] = True
        elif request.method == "DELETE":
            guild.faction_verify[str(factiontid)]["enabled"] = False

    guild.save()

    return jsonify(
        {
            "verify": {
                "enabled": guild.config.get("verify")
                if guild.config.get("verify") is not None
                else False,
                "verify_log_channel": guild.verify_log_channel,
                "faction_verify": guild.faction_verify,
            },
        },
        200,
        {
            "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
            "X-RateLimit-Remaining": client.get(key),
            "X-RateLimit-Reset": client.ttl(key),
        },
    )


@key_required
@ratelimit
@requires_scopes(scopes={"admin", "bot:admin"})
def guild_verification_roles(*args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    client = redisdb.get_redis()
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    guildid = data.get("guildid")
    roles = data.get("roles")

    print(roles)

    if (
        guildid in ("", None, 0)
        or not guildid.isdigit()
    ):
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "GeneralError",
                    "message": "Server failed to fulfill the request. A valid guild ID, faction TID, and role ID are required.",
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )

    guildid = int(guildid)
    guild: ServerModel = ServerModel.objects(sid=guildid).first()

    if guild is None:
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "UnknownGuild",
                    "message": "Server failed to fulfill the request. The guild ID could not be matched with a server "
                    "in the database.",
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )

    try:
        guild.verified_roles = [int(role) for role in roles]
    except ValueError:
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "ValueError",
                    "message": "Server failed to fulfill the request. A role could not be parsed."
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )

    guild.save()

    return jsonify(
        {
            "verify": {
                "enabled": guild.config.get("verify")
                if guild.config.get("verify") is not None
                else False,
                "verify_log_channel": guild.verify_log_channel,
                "faction_verify": guild.faction_verify,
            }
        },
        200,
        {
            "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
            "X-RateLimit-Remaining": client.get(key),
            "X-RateLimit-Reset": client.ttl(key),
        },
    )


@key_required
@ratelimit
@requires_scopes(scopes={"admin", "bot:admin"})
def faction_role(*args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    client = redisdb.get_redis()
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    guildid = data.get("guildid")
    factiontid = data.get("factiontid")
    roleid = data.get("role")

    if (
        guildid in ("", None, 0)
        or not guildid.isdigit()
        or factiontid in ("", None, 0)
        or not factiontid.isdigit()
        or roleid in ("", None, 0)
        or not roleid.isdigit()
    ):
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "GeneralError",
                    "message": "Server failed to fulfill the request. A valid guild ID, faction TID, and role ID are required.",
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )

    guildid = int(guildid)
    factiontid = int(factiontid)
    roleid = int(roleid)

    guild: ServerModel = ServerModel.objects(sid=guildid).first()

    if guild is None:
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "UnknownGuild",
                    "message": "Server failed to fulfill the request. The guild ID could not be matched with a server "
                    "in the database.",
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )

    if str(factiontid) not in guild.faction_verify.keys():
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "GeneralError",
                    "message": "Server failed to fulfill the request. The faction does not have a verification config.",
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )
    elif (
        request.method == "POST"
        and roleid in guild.faction_verify[str(factiontid)]["roles"]
    ) or (
        request.method == "DELETE"
        and roleid not in guild.faction_verify[str(factiontid)]["roles"]
    ):
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "",
                    "message": "Server failed to fulfill the request. Improper HTTP request type.",
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )

    if request.method == "POST":
        guild.faction_verify[str(factiontid)]["roles"].append(roleid)
    elif request.method == "DELETE":
        guild.faction_verify[str(factiontid)]["roles"].remove(roleid)

    guild.save()

    return jsonify(
        {
            "verify": {
                "enabled": guild.config.get("verify")
                if guild.config.get("verify") is not None
                else False,
                "verify_log_channel": guild.verify_log_channel,
                "faction_verify": guild.faction_verify,
            },
        },
        200,
        {
            "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
            "X-RateLimit-Remaining": client.get(key),
            "X-RateLimit-Reset": client.ttl(key),
        },
    )
