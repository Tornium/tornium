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

from tornium_commons.models import ServerModel

from controllers.api.decorators import key_required, ratelimit, requires_scopes
from controllers.api.utils import api_ratelimit_response, make_exception_response


def jsonified_server_config(guild: ServerModel):
    data = {
        "id": str(guild.sid),
        "name": guild.name,
        "admins": guild.admins,
        "factions": guild.factions,
        "stakeouts": {
            "enabled": guild.config.get("stakeouts"),
            "category": guild.stakeoutconfig.get("category"),
            "user_stakeouts": guild.userstakeouts,
            "faction_stakeouts": guild.factionstakeouts,
        },
        "verify": {
            "enabled": guild.config.get("verify"),
            "template": guild.verify_template,
            "verified_roles": list(map(str, guild.verified_roles)),
            "exclusion_roles": list(map(str, guild.exclusion_roles)),
            "faction_verify": guild.faction_verify,
            "log_channel": str(guild.verify_log_channel),
        },
        "retals": dict(zip(guild.retal_config.keys(), map(dict, guild.retal_config.values()))),
        "assists": {
            "channel": str(guild.assistschannel),
            "factions": guild.assist_factions,
            "modifier": guild.assist_mod,
        },
        "oc": guild.oc_config,
    }

    for faction in data["verify"]["faction_verify"]:
        data["verify"]["faction_verify"][faction]["roles"] = list(
            map(str, data["verify"]["faction_verify"][faction]["roles"])
        )

    return data


@key_required
@ratelimit
@requires_scopes(scopes={"admin", "bot:admin"})
def server_config(guildid, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    guild: ServerModel = ServerModel.objects(sid=guildid).first()

    if guild is None:
        return make_exception_response("1001", key)
    elif kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)

    return jsonified_server_config(guild), 200, api_ratelimit_response(key)
