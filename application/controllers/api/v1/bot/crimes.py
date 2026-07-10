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
from uuid import UUID, uuid4

from flask import request
from peewee import DoesNotExist
from tornium_commons.formatters import str_to_duration
from tornium_commons.models import (
    Faction,
    OrganizedCrime,
    OrganizedCrimeSlotType,
    Server,
    ServerOCConfig,
    ServerOCRangeConfig,
)

from controllers.api.v1.decorators import ratelimit, session_required
from controllers.api.v1.utils import api_ratelimit_response, make_exception_response


@session_required
@ratelimit
def set_oc_config_channel(guild_id: int, faction_tid: int, feature: str, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"
    feature = feature.replace("-", "_")

    if feature not in ("tool", "delayed", "missing_member", "extra_range"):
        return make_exception_response("1000", key)

    channel_id = data.get("channel")

    if channel_id is None:
        return make_exception_response("1002", key)
    elif channel_id is not None and (channel_id in ("", 0) or not channel_id.isdigit()):
        return make_exception_response("1002", key)

    try:
        guild: Server = Server.select(Server.sid, Server.admins, Server.factions).where(Server.sid == guild_id).get()
    except DoesNotExist:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)
    elif faction_tid not in guild.factions:
        return make_exception_response("4021", key)

    try:
        faction: Faction = (
            Faction.select(Faction.guild, Faction.has_migrated_oc).where(Faction.tid == faction_tid).get()
        )
    except DoesNotExist:
        return make_exception_response("1102", key)

    if guild.sid != faction.guild_id:
        return make_exception_response("4021", key)
    elif not faction.has_migrated_oc:
        return make_exception_response("4300", key)

    oc_config = ServerOCConfig.create_or_update(guild_id, faction_tid, **{f"{feature}_channel": channel_id})

    return oc_config.to_dict(), 200, api_ratelimit_response(key)


@session_required
@ratelimit
def set_oc_config_roles(guild_id: int, faction_tid: int, feature: str, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"
    feature = feature.replace("-", "_")

    if feature not in ("tool", "delayed", "missing_member", "extra_range"):
        return make_exception_response("1000", key)

    roles = data.get("roles")

    if roles is None:
        return make_exception_response("1002", key)
    elif roles is not None and not isinstance(roles, list):
        return make_exception_response("1003", key)

    try:
        guild: Server = Server.select(Server.sid, Server.admins, Server.factions).where(Server.sid == guild_id).get()
    except DoesNotExist:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)
    elif faction_tid not in guild.factions:
        return make_exception_response("4021", key)

    try:
        faction: Faction = (
            Faction.select(Faction.guild, Faction.has_migrated_oc).where(Faction.tid == faction_tid).get()
        )
    except DoesNotExist:
        return make_exception_response("1102", key)

    if guild.sid != faction.guild_id:
        return make_exception_response("4021", key)
    elif not faction.has_migrated_oc:
        return make_exception_response("4300", key)

    oc_config = ServerOCConfig.create_or_update(
        guild_id, faction_tid, **{f"{feature}_roles": list(set(map(int, roles)))}
    )

    return oc_config.to_dict(), 200, api_ratelimit_response(key)


@session_required
@ratelimit
def set_tool_crimes(guild_id: int, faction_tid: int, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    crimes = data.get("crimes")

    if crimes is None:
        return make_exception_response("1002", key)
    elif crimes is not None and not isinstance(crimes, list):
        return make_exception_response("1003", key)

    if len(set(crimes) - set(OrganizedCrime.oc_names())) != 0:
        # At least one invalid OC name
        return make_exception_response("1105", key)

    try:
        guild: Server = Server.select(Server.sid, Server.admins, Server.factions).where(Server.sid == guild_id).get()
    except DoesNotExist:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)
    elif faction_tid not in guild.factions:
        return make_exception_response("4021", key)

    try:
        faction: Faction = (
            Faction.select(Faction.guild, Faction.has_migrated_oc).where(Faction.tid == faction_tid).get()
        )
    except DoesNotExist:
        return make_exception_response("1102", key)

    if guild.sid != faction.guild_id:
        return make_exception_response("4021", key)
    elif not faction.has_migrated_oc:
        return make_exception_response("4300", key)

    oc_config = ServerOCConfig.create_or_update(guild_id, faction_tid, tool_crimes=list(set(crimes)))

    return oc_config.to_dict(), 200, api_ratelimit_response(key)


@session_required
@ratelimit
def set_delayed_crimes(guild_id: int, faction_tid: int, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    crimes = data.get("crimes")

    if crimes is None:
        return make_exception_response("1002", key)
    elif crimes is not None and not isinstance(crimes, list):
        return make_exception_response("1003", key)

    db_oc_names = [crime.oc_name for crime in OrganizedCrime.select().distinct(OrganizedCrime.oc_name)]
    if len(set(crimes) - set(db_oc_names)) != 0:
        # At least one invalid OC name
        return make_exception_response("1105", key)

    try:
        guild: Server = Server.select(Server.sid, Server.admins, Server.factions).where(Server.sid == guild_id).get()
    except DoesNotExist:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)
    elif faction_tid not in guild.factions:
        return make_exception_response("4021", key)

    try:
        faction: Faction = (
            Faction.select(Faction.guild, Faction.has_migrated_oc).where(Faction.tid == faction_tid).get()
        )
    except DoesNotExist:
        return make_exception_response("1102", key)

    if guild.sid != faction.guild_id:
        return make_exception_response("4021", key)
    elif not faction.has_migrated_oc:
        return make_exception_response("4300", key)

    oc_config = ServerOCConfig.create_or_update(guild_id, faction_tid, delayed_crimes=list(set(crimes)))

    return oc_config.to_dict(), 200, api_ratelimit_response(key)


@session_required
@ratelimit
def set_extra_range_global_minimum(guild_id: int, faction_tid: int, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    try:
        minimum = int(data.get("minimum"))
    except Exception:
        return make_exception_response("1000", key)

    if minimum < 0 or minimum > 100:
        return make_exception_response("1000", key, details={"message": "Minimum CPR must be between 0 and 100"})

    try:
        guild: Server = Server.select(Server.sid, Server.admins, Server.factions).where(Server.sid == guild_id).get()
    except DoesNotExist:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)
    elif faction_tid not in guild.factions:
        return make_exception_response("4021", key)

    try:
        faction: Faction = (
            Faction.select(Faction.guild, Faction.has_migrated_oc).where(Faction.tid == faction_tid).get()
        )
    except DoesNotExist:
        return make_exception_response("1102", key)

    if guild.sid != faction.guild_id:
        return make_exception_response("4021", key)
    elif not faction.has_migrated_oc:
        return make_exception_response("4300", key)

    oc_config = ServerOCConfig.create_or_update(guild_id, faction_tid, extra_range_global_min=minimum)

    return oc_config.to_dict(), 200, api_ratelimit_response(key)


@session_required
@ratelimit
def set_extra_range_global_maximum(guild_id: int, faction_tid: int, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    try:
        maximum = int(data.get("maximum"))
    except Exception:
        return make_exception_response("1000", key)

    if maximum < 0 or maximum > 100:
        return make_exception_response("1000", key, details={"message": "Maximum CPR must be between 0 and 100"})

    try:
        guild: Server = Server.select(Server.sid, Server.admins, Server.factions).where(Server.sid == guild_id).get()
    except DoesNotExist:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)
    elif faction_tid not in guild.factions:
        return make_exception_response("4021", key)

    try:
        faction: Faction = (
            Faction.select(Faction.guild, Faction.has_migrated_oc).where(Faction.tid == faction_tid).get()
        )
    except DoesNotExist:
        return make_exception_response("1102", key)

    if guild.sid != faction.guild_id:
        return make_exception_response("4021", key)
    elif not faction.has_migrated_oc:
        return make_exception_response("4300", key)

    oc_config = ServerOCConfig.create_or_update(guild_id, faction_tid, extra_range_global_max=maximum)

    return oc_config.to_dict(), 200, api_ratelimit_response(key)


@session_required
@ratelimit
def patch_extra_range_local(guild_id: int, faction_id: int, slot_guid: str, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    try:
        slot_type: OrganizedCrimeSlotType = (
            OrganizedCrimeSlotType.select().where(OrganizedCrimeSlotType.guid == UUID(slot_guid)).get()
        )
    except ValueError:
        return make_exception_response(
            "0000", key, details={"element": "slot_guid", "message": "The slot GUID was not a valid UUIDv4."}
        )
    except DoesNotExist:
        return make_exception_response(
            "1000", key, details={"element": "slot_guid", "message": "The provided slot GUID does not exist."}
        )

    minimum_set = "minimum" in data
    minimum = data.get("minimum")
    maximum_set = "maximum" in data
    maximum = data.get("maximum")

    update_kwargs = {}
    if minimum is not None and isinstance(minimum, str) and minimum.isdigit():
        update_kwargs["minimum"] = int(minimum)
    elif minimum is not None and isinstance(minimum, int):
        update_kwargs["minimum"] = minimum
    elif minimum_set and minimum is None:
        update_kwargs["minimum"] = None
    elif maximum is not None and isinstance(maximum, str) and maximum.isdigit():
        update_kwargs["maximum"] = int(maximum)
    elif maximum is not None and isinstance(maximum, int):
        update_kwargs["maximum"] = maximum
    elif maximum_set and maximum is None:
        update_kwargs["maximum"] = None

    try:
        oc_config: ServerOCConfig = (
            ServerOCConfig.select(ServerOCConfig.guid)
            .where((ServerOCConfig.server == guild_id) & (ServerOCConfig.faction == faction_id))
            .get()
        )
    except DoesNotExist:
        return make_exception_response("1000", key, details={"message": "Server OC configuration does not exist"})

    range_config: ServerOCRangeConfig = (
        ServerOCRangeConfig.insert(
            guid=uuid4(),
            server_oc_config_id=oc_config.guid,
            oc_type_id=slot_type.oc_type_id,
            oc_slot_type_id=slot_type.guid,
            **update_kwargs,
        )
        .on_conflict(
            conflict_target=[
                ServerOCRangeConfig.server_oc_config_id,
                ServerOCRangeConfig.oc_type_id,
                ServerOCRangeConfig.oc_slot_type_id,
            ],
            preserve=list(update_kwargs.keys()),
        )
        .returning(ServerOCRangeConfig)
        .execute()[0]
    )

    if range_config.minimum is None and range_config.maximum is None:
        range_config.delete_instance()
        return "", 204, api_ratelimit_response(key)

    return range_config.to_dict(), 200, api_ratelimit_response(key)


@session_required
@ratelimit
def set_missing_member_duration(guild_id: int, faction_tid: int, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    try:
        minimum_duration: datetime.timedelta = str_to_duration(data["minimum_duration"])
    except KeyError:
        return make_exception_response("0000", key, details={"message": "No minimum duration was included."})
    except ValueError as e:
        return make_exception_response("0000", key, details={"message": str(e)})

    if minimum_duration.total_seconds() < 43200:
        return make_exception_response(
            "0000", key, details={"message": "The minimum duration must be at least 6 hours."}
        )

    try:
        guild: Server = Server.select(Server.sid, Server.admins, Server.factions).where(Server.sid == guild_id).get()
    except DoesNotExist:
        return make_exception_response("1001", key)

    if kwargs["user"].tid not in guild.admins:
        return make_exception_response("4020", key)
    elif faction_tid not in guild.factions:
        return make_exception_response("4021", key)

    try:
        faction: Faction = (
            Faction.select(Faction.guild, Faction.has_migrated_oc).where(Faction.tid == faction_tid).get()
        )
    except DoesNotExist:
        return make_exception_response("1102", key)

    if guild.sid != faction.guild_id:
        return make_exception_response("4021", key)
    elif not faction.has_migrated_oc:
        return make_exception_response("4300", key)

    oc_config = ServerOCConfig.create_or_update(guild_id, faction_tid, missing_member_minimum_duration=minimum_duration)

    return oc_config.to_dict(), 200, api_ratelimit_response(key)
