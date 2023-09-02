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
import typing

from flask import jsonify
from tornium_commons.models import FactionModel, ServerModel

from controllers.api.decorators import ratelimit, token_required
from controllers.api.utils import api_ratelimit_response, make_exception_response


def _faction_data(tid, guild=None):
    faction: typing.Optional[FactionModel] = FactionModel.objects(tid=tid).first()

    data = {
        "id": tid,
        "name": "",
    }

    if faction is not None:
        data["name"] = faction.name

    return data


def jsonified_server_config(guild: ServerModel):
    data = {
        "id": str(guild.sid),
        "name": guild.name,
        "admins": guild.admins,
        "factions": {tid: _faction_data(tid) for tid in guild.factions},
        "verify": {
            "enabled": guild.config.get("verify"),
            "template": guild.verify_template,
            "verified_roles": list(map(str, guild.verified_roles)),
            "exclusion_roles": list(map(str, guild.exclusion_roles)),
            "faction_verify": guild.faction_verify,
            "log_channel": str(guild.verify_log_channel),
        },
        "retals": dict(zip(guild.retal_config.keys(), map(dict, guild.retal_config.values()))),
        "banking": guild.banking_config,
        "armory": {"enabled": guild.armory_enabled, "config": {**guild.armory_config}},
        "assists": {
            "channel": str(guild.assistschannel),
            "factions": guild.assist_factions,
            "roles": {
                "smoker": list(map(str, guild.assist_smoker_roles)),
                "tear": list(map(str, guild.assist_tear_roles)),
                "l0": list(map(str, guild.assist_l0_roles)),
                "l1": list(map(str, guild.assist_l1_roles)),
                "l2": list(map(str, guild.assist_l2_roles)),
                "l3": list(map(str, guild.assist_l3_roles)),
            },
        },
        "oc": {
            faction_id: {
                "ready": {
                    "channel": faction_oc_config.get("ready", {"channel": 0}).get("channel", 0),
                    "roles": faction_oc_config.get("ready", {"roles": []}).get("roles", []),
                },
                "delay": {
                    "channel": faction_oc_config.get("delay", {"channel": 0}).get("channel", 0),
                    "roles": faction_oc_config.get("delay", {"roles": 0}).get("roles", []),
                },
                "initiated": {
                    "channel": faction_oc_config.get("initiated", {"channel": 0}).get("channel", 0),
                },
            }
            for faction_id, faction_oc_config in guild.oc_config.items()
        },
        "stocks": {
            "channel": str(guild.stocks_channel),
            **guild.stocks_config,
        },
    }

    for faction in data["verify"]["faction_verify"]:
        data["verify"]["faction_verify"][faction]["roles"] = list(
            map(str, data["verify"]["faction_verify"][faction]["roles"])
        )

    return jsonify(data)


@token_required
@ratelimit
def server_config(guildid, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    guild: ServerModel = ServerModel.objects(sid=guildid).first()

    if guild is None:
        return make_exception_response("1001", key)
    elif kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)

    return jsonified_server_config(guild), 200, api_ratelimit_response(key)
