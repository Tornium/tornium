# Copyright (C) 2021-2025 tiksan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import datetime
import json

from flask import jsonify, request
from liquid.exceptions import LiquidSyntaxError
from peewee import fn, DoesNotExist
from tornium_celery.tasks.guild import _VertificationNameEnvironment
from tornium_commons.models import Faction, Server, User, VerificationLog, VerificationLogResult

from controllers.api.v1.decorators import ratelimit, session_required
from controllers.api.v1.utils import api_ratelimit_response, get_list, make_exception_response

_verification_log_results = (result.value for result in VerificationLogResult)


def jsonified_verify_config(guild: Server):
    return jsonify(
        {
            "enabled": guild.verify_enabled,
            "automatic_enabled": guild.auto_verify_enabled,
            "gateway_verify_enabled": guild.gateway_verify_enabled,
            "verify_template": guild.verify_template,
            "verified_roles": guild.verified_roles,
            "unverified_roles": guild.unverified_roles,
            "exclusion_roles": guild.exclusion_roles,
            "faction_verify": guild.faction_verify,
            "verify_log_channel": guild.verify_log_channel,
            "verify_jail_channel": guild.verify_jail_channel,
        }
    )


@session_required
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

    Server.update(faction_verify=guild.faction_verify).where(Server.sid == guild.sid).execute()

    return jsonified_verify_config(guild), 200, api_ratelimit_response(key)


@session_required
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
            Server.update(verify_enabled=True).where(Server.sid == guild.sid).execute()
        else:
            return make_exception_response(
                "0000",
                key,
                details={
                    "message": "Setting already enabled.",
                    "setting": "guild.verify_enabled",
                },
            )
    elif request.method == "DELETE":
        if guild.verify_enabled:
            guild.verify_enabled = False
            Server.update(verify_enabled=False).where(Server.sid == guild.sid).execute()
        else:
            return make_exception_response(
                "0000",
                key,
                details={
                    "message": "Setting already disabled.",
                    "setting": "guild.verify_enabled",
                },
            )

    return jsonified_verify_config(guild), 200, api_ratelimit_response(key)


@session_required
@ratelimit
def guild_auto_verification(*args, **kwargs):
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
        if not guild.auto_verify_enabled:
            guild.auto_verify_enabled = True
            Server.update(auto_verify_enabled=True).where(Server.sid == guild.sid).execute()
        else:
            return make_exception_response(
                "0000",
                key,
                details={
                    "message": "Setting already enabled.",
                    "setting": "guild.auto_verify_enabled",
                },
            )
    elif request.method == "DELETE":
        if guild.auto_verify_enabled:
            guild.auto_verify_enabled = False
            Server.update(auto_verify_enabled=False).where(Server.sid == guild.sid).execute()
        else:
            return make_exception_response(
                "0000",
                key,
                details={
                    "message": "Setting already disabled.",
                    "setting": "guild.auto_verify_enabled",
                },
            )

    return jsonified_verify_config(guild), 200, api_ratelimit_response(key)


@session_required
@ratelimit
def guild_gateway_verification(guild_id: int, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    try:
        guild: Server = Server.select().where(Server.sid == guild_id).get()
    except DoesNotExist:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)

    if request.method == "POST":
        if not guild.gateway_verify_enabled:
            guild.gateway_verify_enabled = True
            Server.update(gateway_verify_enabled=True).where(Server.sid == guild.sid).execute()
        else:
            return make_exception_response(
                "0000",
                key,
                details={
                    "message": "Setting already enabled.",
                    "setting": "guild.gateway_verify_enabled",
                },
            )
    elif request.method == "DELETE":
        if guild.auto_verify_enabled:
            guild.gateway_verify_enabled = False
            Server.update(gateway_verify_enabled=False).where(Server.sid == guild.sid).execute()
        else:
            return make_exception_response(
                "0000",
                key,
                details={
                    "message": "Setting already disabled.",
                    "setting": "guild.gateway_verify_enabled",
                },
            )

    return jsonified_verify_config(guild), 200, api_ratelimit_response(key)


@session_required
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
    Server.update(verify_log_channel=channel_id).where(Server.sid == guild.sid).execute()

    return jsonified_verify_config(guild), 200, api_ratelimit_response(key)


@session_required
@ratelimit
def guild_jail_channel(guild_id: int, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    try:
        channel_id = int(data["channel"])
    except (KeyError, ValueError, TypeError):
        return make_exception_response("1001", key)

    try:
        guild: Server = Server.select().where(Server.sid == guild_id).get()
    except DoesNotExist:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)

    guild.verify_jail_channel = channel_id
    Server.update(verify_jail_channel=channel_id).where(Server.sid == guild.sid).execute()

    return jsonified_verify_config(guild), 200, api_ratelimit_response(key)


@session_required
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
        _VertificationNameEnvironment().render(template, name="tiksan", tid=2383326, tag="NSO").strip()
    except LiquidSyntaxError:
        return make_exception_response(
            "1000",
            key,
            details={
                "element": "template",
                "message": "The provided template could not be parsed/rendered by the Liquid templating engine",
            },
        )

    try:
        guild: Server = Server.get_by_id(guild_id)
    except DoesNotExist:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)

    guild.verify_template = template
    Server.update(verify_template=guild.verify_template).where(Server.sid == guild.sid).execute()

    return jsonified_verify_config(guild), 200, api_ratelimit_response(key)


@session_required
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

    Server.update(faction_verify=guild.faction_verify).where(Server.sid == guild.sid).execute()

    return jsonified_verify_config(guild), 200, api_ratelimit_response(key)


@session_required
@ratelimit
def guild_verification_roles(*args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    roles = data.get("roles")

    if roles is None or not isinstance(roles, list):
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


@session_required
@ratelimit
def guild_unverified_roles(*args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    roles = data.get("roles")

    if roles is None or not isinstance(roles, list):
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
        guild.unverified_roles = [int(role) for role in roles]
    except ValueError:
        return make_exception_response("1003", key)

    Server.update(unverified_roles=guild.unverified_roles).where(Server.sid == guild.sid).execute()

    return jsonified_verify_config(guild), 200, api_ratelimit_response(key)


@session_required
@ratelimit
def guild_exclusion_roles(*args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    roles = data.get("roles")

    if roles is None or not isinstance(roles, list):
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

    Server.update(exclusion_roles=guild.exclusion_roles).where(Server.sid == guild.sid).execute()

    return jsonified_verify_config(guild), 200, api_ratelimit_response(key)


@session_required
@ratelimit
def faction_roles(faction_tid, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    roles = data.get("roles")

    if roles is None or not isinstance(roles, list):
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
    Server.update(faction_verify=guild.faction_verify).where(Server.sid == guild.sid).execute()

    return jsonified_verify_config(guild), 200, api_ratelimit_response(key)


@session_required
@ratelimit
def faction_position_roles(faction_tid: int, position: str, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    roles = data.get("roles")

    if roles is None or not isinstance(roles, list):
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
    Server.update(faction_verify=guild.faction_verify).where(Server.sid == guild.sid).execute()

    return jsonified_verify_config(guild), 200, api_ratelimit_response(key)


@session_required
@ratelimit
def verify_logs(guild_id: int, *args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"
    user: User = kwargs["user"]

    try:
        guild: Server = Server.select(Server.admins).where(Server.sid == int(guild_id)).get()
    except (ValueError, TypeError, DoesNotExist):
        return make_exception_response("1001", key)

    if user.tid not in guild.admins:
        return make_exception_response("4020", key)

    now = int(datetime.datetime.utcnow().timestamp())

    try:
        limit = int(request.args.get("limit", 25))
        offset = int(request.args.get("offset", 0))
        from_timestamp = int(request.args.get("from", 0))
        to_timestamp = int(request.args.get("to", now))
        sort_order = request.args.get("sort", "timestamp-desc")
    except (TypeError, ValueError):
        return make_exception_response("1000", key)

    results = get_list(request.args, "results", str)

    if limit < 0 or limit > 100:
        return make_exception_response(
            "0000", key, details={"element": "limit", "message": "The limit must be between 0 and 100."}
        )
    elif offset < 0:
        return make_exception_response(
            "0000", key, detils={"element": "offset", "message": "The offset must be greater than or equal to 0."}
        )
    elif len(results) > 0 and any([result not in _verification_log_results for result in results]):
        return make_exception_response(
            "0000", key, details={"element": "results", "message": "There was an invalid result provided."}
        )
    elif from_timestamp < 0 or from_timestamp > now:
        return make_exception_response(
            "0000", key, details={"element": "from", "message": "There was an invalid from timestamp provided."}
        )
    elif to_timestamp <= 0 or to_timestamp > now:
        return make_exception_response(
            "0000", key, details={"element": "to", "message": "There was an invalid to timestamp provided."}
        )
    elif from_timestamp > to_timestamp:
        return make_exception_response(
            "0000",
            key,
            details={"element": "from+to", "message": "The from timestamp can not be larger than the to timstamp."},
        )

    logs = VerificationLog.select().where(VerificationLog.server_id == guild_id)

    # if len(results) != 0:
    #     logs = logs.where(VerificationLog.result.in_(members))
    if from_timestamp != 0:
        logs = logs.where(
            VerificationLog.timestamp >= datetime.datetime.fromtimestamp(from_timestamp, tz=datetime.timezone.utc)
        )
    if to_timestamp != now:
        logs = logs.where(
            VerificationLog.timestamp <= datetime.datetime.fromtimestamp(to_timestamp, tz=datetime.timezone.utc)
        )

    if sort_order == "timestamp-desc":
        logs = logs.order_by(VerificationLog.timestamp.desc())
    elif sort_order == "timestamp-asc":
        logs = logs.order_by(VerificationLog.timestamp.asc())
    else:
        return make_exception_response(
            "0000",
            key,
            details={
                "element": "sort",
                "message": 'The sort order must be one of the following: "timestamp-desc" or "timestamp-asc".',
            },
        )

    total_count_expression = fn.COUNT(VerificationLog.guid).over()
    logs = logs.select(VerificationLog, total_count_expression.alias("total_count"))
    paged_logs = list(logs.limit(limit).offset(offset))
    total_count = paged_logs[0].total_count if paged_logs else 0

    return (
        {"count": total_count, "logs": [log.to_dict() for log in paged_logs]},
        200,
        api_ratelimit_response(key),
    )
