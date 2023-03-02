# Copyright (C) 2021-2023 tiksan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import datetime
import json

from flask import jsonify, request

from tornium_celery.tasks.api import discordpost
from tornium_commons.models import FactionStakeoutModel, KeyModel, ServerModel, UserStakeoutModel

from controllers.api.decorators import key_required, ratelimit, requires_scopes
from controllers.api.utils import api_ratelimit_response, make_exception_response
from models.stakeout import Stakeout
from models.user import User


@key_required
@ratelimit
@requires_scopes(scopes={"admin", "write:stakeouts", "guilds:admin"})
def create_stakeout(stype, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f'tornium:ratelimit:{kwargs["user"].tid}'

    guildid = data.get("guildid")
    tid = data.get("tid")
    keys = data.get("keys")
    name = data.get("name")
    category = data.get("category")

    if guildid is None:
        return make_exception_response("1001", key)
    elif tid is None:
        return make_exception_response("1000", key)

    guildid = int(guildid)
    tid = int(tid)
    guild: ServerModel = ServerModel.objects(sid=guildid).first()

    if stype not in ["faction", "user"]:
        return make_exception_response(
            "1000",
            key,
            details={
                "message": "The provided stakeout type did not match a known stakeout type.",
                "stakeout_category": stype,
            },
        )
    elif User(KeyModel.objects(key=kwargs["key"]).first().ownertid).tid not in guild.admins:
        return make_exception_response("1001", key)
    if json.loads(guild.config)["stakeoutconfig"] != 1:
        return make_exception_response(
            "0000",
            key,
            details={"message": "Server admins have not enabled stakeouts."},
        )
    elif (
        stype == "user"
        and UserStakeoutModel.objects(tid=tid).first() is not None
        and str(guildid) in UserStakeoutModel.objects(tid=tid).first().guilds
    ):
        return make_exception_response("0000", key, details={"message": "Stakeout already exists."})
    elif (
        stype == "faction"
        and FactionStakeoutModel.objects(tid=tid).first() is not None
        and str(guildid) in FactionStakeoutModel.objects(tid=tid).first().guilds
    ):
        return make_exception_response("0000", key, details={"message": "Stakeout already exists."})
    elif (
        stype == "user"
        and keys is not None
        and not set(keys) & {"level", "status", "flyingstatus", "online", "offline"}
    ):
        return make_exception_response("0000", key, details={"message": "Invalid stakeout key."})
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
        return make_exception_response("0000", key, details={"message": "Invalid stakeout key."})

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

    channel = discordpost(f"guilds/{guildid}/channels", payload=payload)

    stakeout.guilds[str(guildid)]["channel"] = int(channel["id"])

    if stype == "user":
        db_stakeout = UserStakeoutModel.objects(tid=tid).first()
        message_payload = {
            "embeds": [
                {
                    "title": "User Stakeout Creation",
                    "description": f'A stakeout of user {stakeout.data["name"]} has been created in '
                    f"{guild.name}. This stakeout can be setup or removed in the "
                    f"[Tornium Dashboard](https://tornium.com/bot/stakeouts/{guild.sid}) by a "
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
                    f"[Tornium Dashboard](https://tornium.com/bot/stakeouts/{guild.sid}) by a "
                    f"server administrator.",
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                }
            ]
        }

    db_stakeout.guilds = stakeout.guilds
    db_stakeout.save()
    discordpost(f'channels/{channel["id"]}/messages', payload=message_payload)

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
        api_ratelimit_response(key),
    )
