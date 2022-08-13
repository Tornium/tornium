# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import json

from controllers.api.decorators import *
from models.factionstakeoutmodel import FactionStakeoutModel
from models.keymodel import KeyModel
from models.servermodel import ServerModel
from models.stakeout import Stakeout
from models.user import User
from models.userstakeoutmodel import UserStakeoutModel
import tasks
import utils


@key_required
@ratelimit
@requires_scopes(scopes={"admin", "write:stakeouts", "guilds:admin"})
def create_stakeout(stype, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    client = redisdb.get_redis()
    key = f'tornium:ratelimit:{kwargs["user"].tid}'

    guildid = data.get("guildid")
    tid = data.get("tid")
    keys = data.get("keys")
    name = data.get("name")
    category = data.get("category")

    if guildid is None:
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "UnknownGuild",
                    "message": "Server failed to fulfill the request. There was no guild ID provided but a guild ID was "
                    "required.",
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )
    elif tid is None:
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "UnknownID",
                    "message": "Server failed to fulfill the request. There was no Torn ID provided but a Torn ID was "
                    "required.",
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
    tid = int(tid)
    guild: ServerModel = ServerModel.objects(sid=guildid).first()

    if stype not in ["faction", "user"]:
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "InvalidStakeoutType",
                    "message": "Server failed to create the stakeout. The provided stakeout type did not match a known "
                    "stakeout type.",
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
        str(guildid)
        not in User(KeyModel.objects(key=kwargs["key"]).first().ownertid).servers
    ):
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "UnknownGuild",
                    "message": "Server failed to fulfill the request. The provided guild ID did not match a guild that the "
                    "owner of the provided Tornium key was marked as an administrator in.",
                }
            ),
            403,
            {
                "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )
    if json.loads(guild.config)["stakeoutconfig"] != 1:
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "InvalidRequest",
                    "message": "Server failed to fulfill the request. The provided server ID has not enabled stakeouts. "
                    "Contact a server administrator in order to enable this feature.",
                }
            ),
            403,
            {
                "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )
    elif (
        stype == "user"
        and UserStakeoutModel.objects(tid=tid).first() is not None
        and str(guildid) in UserStakeoutModel.objects(tid=tid).first().guilds
    ):
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "StakeoutAlreadyExists",
                    "message": "Server failed to fulfill the request. The provided user ID is already being staked",
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
        stype == "faction"
        and FactionStakeoutModel.objects(tid=tid).first() is not None
        and str(guildid) in FactionStakeoutModel.objects(tid=tid).first().guilds
    ):
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "StakeoutAlreadyExists",
                    "message": "Server failed to fulfill the request. The provided faction ID is already being staked",
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
        stype == "user"
        and keys is not None
        and not set(keys) & {"level", "status", "flyingstatus", "online", "offline"}
    ):
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "InvalidStakeoutKey",
                    "message": "Server failed to fulfill the request. The provided array of stakeout keys included a "
                    "stakeout key that was invalid for the provided stakeout type..",
                }
            ),
            403,
            {
                "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )
    elif (
        stype == "faction"
        and keys is not None
        and not set(keys)
        & {
            "territory",
            "members",
            "memberstatus",
            "memberactivity",
            "armory",
            "assault",
            "armorydeposit",
        }
    ):
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "InvalidStakeoutKey",
                    "message": "Server failed to fulfill the request. The provided array of stakeout keys included a "
                    "stakeout key that was invalid for the provided stakeout type..",
                }
            ),
            403,
            {
                "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )

    stakeout = Stakeout(
        tid=tid,
        guild=guildid,
        user=True if stype == "user" else False,
        key=kwargs["user"].key,
    )

    if stype == "user":
        stakeouts = guild.userstakeouts
        stakeouts.append(tid)
        guild.userstakeouts = list(set(stakeouts))
        guild.save()
    elif stype == "faction":
        stakeouts = guild.factionstakeouts
        stakeouts.append(tid)
        guild.factionstakeouts = list(set(stakeouts))
        guild.save()

    payload = {
        "name": f'{stype}-{stakeout.data["name"]}' if name is None else name,
        "type": 0,
        "topic": f'The bot-created channel for stakeout notifications for {stakeout.data["name"]} '
        f'[{stakeout.data["player_id"] if stype == "user" else stakeout.data["ID"]}] by the Tornium bot.',
        "parent_id": guild.stakeoutconfig["category"] if category is None else category,
    }

    channel = tasks.discordpost(
        f"guilds/{guildid}/channels", payload=payload, dev=guild.skynet
    )

    stakeout.guilds[str(guildid)]["channel"] = int(channel["id"])
    if stype == "user":
        db_stakeout = UserStakeoutModel.objects(tid=tid).first()
        message_payload = {
            "embeds": [
                {
                    "title": "User Stakeout Creation",
                    "description": f'A stakeout of user {stakeout.data["name"]} has been created in '
                    f"{guild.name}. This stakeout can be setup or removed in the "
                    f"[Tornium Dashboard](https://torn.deek.sh/bot/stakeouts/{guild.sid}) by a "
                    f"server administrator.",
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                }
            ]
        }
    elif stype == "faction":
        db_stakeout = FactionStakeoutModel.objects(tid=tid).first()
        message_payload = {
            "embeds": [
                {
                    "title": "Faction Stakeout Creation",
                    "description": f'A stakeout of faction {stakeout.data["name"]} has been created in '
                    f"{guild.name}. This stakeout can be setup or removed in the "
                    f"[Tornium Dashboard](https://torn.deek.sh/bot/stakeouts/{guild.sid}) by a "
                    f"server administrator.",
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                }
            ]
        }

    db_stakeout.guilds = stakeout.guilds
    db_stakeout.save()
    tasks.discordpost(
        f'channels/{channel["id"]}/messages', payload=message_payload, dev=guild.skynet
    )

    return (
        jsonify(
            {
                "id": tid,
                "type": stype,
                "config": json.loads(db_stakeout.guilds)[str(guildid)],
                "data": stakeout.data,
                "last_update": stakeout.last_update,
            }
        ),
        200,
        {
            "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
            "X-RateLimit-Remaining": client.get(key),
            "X-RateLimit-Reset": client.ttl(key),
        },
    )
