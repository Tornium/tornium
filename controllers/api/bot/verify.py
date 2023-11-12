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

import json

from flask import jsonify, request
from peewee import DoesNotExist
from tornium_commons.models import Faction, Server

from controllers.api.decorators import ratelimit, token_required
from controllers.api.utils import api_ratelimit_response, make_exception_response


def jsonified_verify_config(guild: Server):
    return jsonify(
        {
            "enabled": guild.verify_enabled,
            "verify_template": guild.verify_template,
            "verified_roles": guild.verified_roles,
            "faction_verify": guild.faction_verify,
            "verify_log_channel": guild.verify_log_channel,
        }
    )


@token_required
@ratelimit
def verification_config(guild_id, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    try:
        guild: Server = Server.get_by_id(guild_id)
    except DoesNotExist:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)

    for faction_tid, faction_data in guild.faction_verify.items():
        if "positions" not in guild.faction_verify[faction_tid]:
            guild.faction_verify[faction_tid]["positions"] = {}

    guild.save()

    return jsonified_verify_config(guild), 200, api_ratelimit_response(key)


@token_required
@ratelimit
def guild_verification(*args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    try:
        guild_id = int(data["guildid"])
    except (KeyError, ValueError, TypeError):
        return make_exception_response("1001", key)

    try:
        guild: Server = Server.get_by_id(guild_id)
    except DoesNotExist:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)

    # TODO: Replace below error messages

    if request.method == "POST":
        if not guild.verify_enabled:
            guild.verify_enabled = True
            guild.save()
        else:
            return make_exception_response(
                "0000",
                key,
                details={
                    "message": "Setting already enabled.",
                    "setting": "guild.config.verify",
                },
            )
    elif request.method == "DELETE":
        if guild.config.verify_enabled:
            guild.verify_enabled = False
            guild.save()
        else:
            return make_exception_response(
                "0000",
                key,
                details={
                    "message": "Setting already disabled.",
                    "setting": "guild.config.verify",
                },
            )

    return jsonified_verify_config(guild), 200, api_ratelimit_response(key)


@token_required
@ratelimit
def guild_verification_log(*args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    try:
        guild_id = int(data["guildid"])
    except (KeyError, ValueError, TypeError):
        return make_exception_response("1001", key)

    try:
        channel_id = int(data["channel"])
    except (KeyError, ValueError, TypeError):
        return make_exception_response("1001", key)

    try:
        guild: Server = Server.get_by_id(guild_id)
    except DoesNotExist:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)

    guild.verify_log_channel = channel_id
    guild.save()

    return jsonified_verify_config(guild), 200, api_ratelimit_response(key)


@token_required
@ratelimit
def guild_verification_template(*args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    try:
        guild_id = int(data["guildid"])
    except (KeyError, ValueError, TypeError):
        return make_exception_response("1001", key)

    try:
        template = data["template"]
    except KeyError:
        return make_exception_response("1000", key, details={"element": "template"})

    try:
        guild: Server = Server.get_by_id(guild_id)
    except DoesNotExist:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)

    guild.verify_template = template
    guild.save()

    return jsonified_verify_config(guild), 200, api_ratelimit_response(key)


@token_required
@ratelimit
def faction_verification(*args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f'tornium:ratelimit:{kwargs["user"].tid}'

    try:
        guild_id = int(data["guildid"])
    except (KeyError, ValueError, TypeError):
        return make_exception_response("1001", key)

    try:
        faction_tid = int(data["factiontid"])
    except (KeyError, ValueError, TypeError):
        return make_exception_response("1002", key)

    try:
        guild: Server = Server.get_by_id(guild_id)
    except DoesNotExist:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)

    try:
        faction: Faction = Faction.get_by_id(faction_tid)
    except DoesNotExist:
        return make_exception_response("1102", key)

    if request.method == "DELETE" and str(faction.tid) not in guild.faction_verify:
        return make_exception_response(
            "0000",
            key,
            details={
                "message": "Faction not in guild's list of factions to verify.",
                "factiontid": faction_tid,
            },
        )

    if request.method == "DELETE" and data.get("remove") is True:
        del guild.faction_verify[str(faction_tid)]
    else:
        if faction.tid not in guild.faction_verify:
            guild.faction_verify[str(faction_tid)] = {
                "roles": [],
                "positions": {},
                "enabled": False,
            }

        if request.method == "POST":
            guild.faction_verify[str(faction_tid)]["enabled"] = True
        elif request.method == "DELETE":
            guild.faction_verify[str(faction_tid)]["enabled"] = False

    guild.save()

    return jsonified_verify_config(guild), 200, api_ratelimit_response(key)


@token_required
@ratelimit
def guild_verification_roles(*args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    roles = data.get("roles")

    if roles is None or type(roles) != list:
        return make_exception_response("1000", key)

    try:
        guild_id = int(data["guildid"])
    except (KeyError, ValueError, TypeError):
        return make_exception_response("1001", key)

    try:
        guild: Server = Server.get_by_id(guild_id)
    except DoesNotExist:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)

    try:
        guild.verified_roles = [int(role) for role in roles]
    except ValueError:
        return make_exception_response("1003", key)

    guild.save()

    return jsonified_verify_config(guild), 200, api_ratelimit_response(key)


@token_required
@ratelimit
def guild_exclusion_roles(*args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    roles = data.get("roles")

    if roles is None or type(roles) != list:
        return make_exception_response("1000", key)

    try:
        guild_id = int(data["guildid"])
    except (KeyError, ValueError, TypeError):
        return make_exception_response("1001", key)

    try:
        guild: Server = Server.get_by_id(guild_id)
    except DoesNotExist:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)

    try:
        guild.exclusion_roles = [int(role) for role in roles]
    except ValueError:
        return make_exception_response("1003", key)

    guild.save()

    return jsonified_verify_config(guild), 200, api_ratelimit_response(key)


@token_required
@ratelimit
def faction_roles(faction_tid, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    roles = data.get("roles")

    if roles is None or type(roles) != list:
        return make_exception_response("1000", key)

    try:
        guild_id = int(data["guildid"])
    except (KeyError, ValueError, TypeError):
        return make_exception_response("1001", key)

    try:
        guild: Server = Server.get_by_id(guild_id)
    except DoesNotExist:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)
    elif str(faction_tid) not in guild.faction_verify.keys():
        return make_exception_response("1102", key)

    guild.faction_verify[str(faction_tid)]["roles"] = [int(role) for role in roles]
    guild.save()

    return jsonified_verify_config(guild), 200, api_ratelimit_response(key)


@token_required
@ratelimit
def faction_position_roles(faction_tid: int, position: str, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    roles = data.get("roles")

    if roles is None or type(roles) != list:
        return make_exception_response("1000", key)

    try:
        guild_id = int(data["guildid"])
    except (KeyError, ValueError, TypeError):
        return make_exception_response("1001", key)

    try:
        guild: Server = Server.get_by_id(guild_id)
    except DoesNotExist:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)
    elif str(faction_tid) not in guild.faction_verify.keys():
        return make_exception_response("1102", key)

    guild.faction_verify[str(faction_tid)]["positions"][position] = roles
    guild.save()

    return jsonified_verify_config(guild), 200, api_ratelimit_response(key)
