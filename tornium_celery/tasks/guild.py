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
import inspect
import logging
import math
import random
import time
import typing

import celery
import jinja2
from celery.utils.log import get_task_logger
from tornium_commons import rds
from tornium_commons.errors import DiscordError, NetworkingError
from tornium_commons.formatters import torn_timestamp
from tornium_commons.models import PositionModel, ServerModel, UserModel
from tornium_commons.skyutils import SKYNET_ERROR, SKYNET_INFO

from .api import discordget, discordpatch, discordpost, tornget

logger: logging.Logger = get_task_logger(__name__)


@celery.shared_task(name="tasks.guild.refresh_guilds", routing_key="default.refresh_guilds", queue="default")
def refresh_guilds():
    try:
        guilds = discordget("users/@me/guilds")
    except Exception as e:
        logger.exception(e)
        return

    guilds_not_updated = [int(server.sid) for server in ServerModel.objects()]

    for guild in guilds:
        if int(guild["id"]) in guilds_not_updated:
            guilds_not_updated.remove(int(guild["id"]))

        guild_db: ServerModel = ServerModel.objects(sid=guild["id"]).first()

        if guild_db is None:
            guild_db = ServerModel(
                sid=guild["id"],
                name=guild["name"],
                admins=[],
                config={"stakeouts": 0, "verify": 0},
                icon=guild["icon"],
                factions=[],
                stakeoutconfig={"category": 0},
                userstakeouts=[],
                factionstakeouts=[],
                assistschannel=0,
                assist_factions=[],
                assist_mod=0,
            )
            guild_db.save()

        try:
            members = discordget(f'guilds/{guild["id"]}/members?limit=1000')
        except DiscordError as e:
            if e.code == 10007:
                continue
            else:
                logger.exception(e)
                continue
        except Exception as e:
            logger.exception(e)
            continue

        try:
            guild = discordget(f'guilds/{guild["id"]}')
        except Exception as e:
            logger.exception(e)
            continue

        admins = []
        owner: UserModel = UserModel.objects(discord_id=guild["owner_id"]).first()

        if owner is not None:
            admins.append(owner.tid)

        for member in members:
            user: UserModel = UserModel.objects(discord_id=member["user"]["id"]).first()

            if user is not None and user.key not in (None, ""):
                for role in member["roles"]:
                    for guild_role in guild["roles"]:
                        # Checks if the user has the role and the role has the administrator permission
                        if guild_role["id"] == role and (int(guild_role["permissions"]) & 0x0000000008) == 0x0000000008:
                            admins.append(user.tid)

        admins = list(set(admins))
        guild_db.admins = admins
        guild_db.icon = guild["icon"]
        guild_db.save()

        for factiontid, faction_data in guild_db.faction_verify.items():
            faction_positions_data = faction_data

            if "positions" not in faction_data:
                continue

            for position_uuid, position_data in faction_data["positions"].items():
                position: PositionModel = PositionModel.objects(pid=position_uuid).first()

                if position is None or position.factiontid != int(factiontid):
                    faction_positions_data["positions"].pop(position_uuid)

            guild_db.faction_verify[factiontid] = faction_positions_data

        guild_db.save()

    for deleted_guild in guilds_not_updated:
        guild: ServerModel = ServerModel.objects(sid=deleted_guild).first()

        if guild is None:
            continue

        logger.info(f"Deleted {guild.name} [{guild.sid}] from database (Reason: not found by Discord API)")
        guild.delete()


@celery.shared_task(name="tasks.guild.verify_users", routing_key="default.verify_users", queue="default")
def verify_users(
    guild_id: int, admin_keys: typing.Optional[set] = None, force=False, highest_id: int = 0, log_channel: int = -2
):
    # Log channel
    # -2: temporarily disabled (to be verified)
    # -1: disabled
    #  n: channel ID

    guild: typing.Optional[ServerModel] = ServerModel.objects(sid=guild_id).first()

    if guild is None:
        raise LookupError
    elif guild.config.get("verify") in (None, 0):
        return ValueError("Verification not enabled")
    elif guild.verify_template == "" and len(guild.verified_roles) == 0 and len(guild.faction_verify) == 0:
        return ValueError("Verification will result in no state change")

    redis_client = rds()

    if redis_client.exists(f"tornium:verify:{guild.sid}:lock") and highest_id == 0:
        raise RuntimeError(f"Run in {redis_client.ttl(f'tornium:verify:{guild.sid}:lock')} seconds")

    redis_client.set(f"tornium:verify:{guild.sid}:lock", 1, ex=600, nx=True)

    if admin_keys is None:
        admin_keys = tuple([admin.key for admin in guild.admins if admin is not None and admin.key not in ("", None)])

    server_data = discordget(
        f"guilds/{guild.sid}?with_counts=true",
    )

    redis_client.set(f"tornium:verify:{guild.sid}:member_count", 0, ex=600, nx=True)
    redis_client.set(f"tornium:verify:{guild.sid}:member_fetch_runs", 0, ex=600, nx=True)
    redis_client.set(f"tornium:verify:{guild.sid}:errors", 0, ex=600, nx=True)

    if log_channel == -2:
        if guild.verify_log_channel in ("", None, 0):
            redis_client.set(f"tornium:verify:{guild.sid}:log_channel", -1, ex=600)
            log_channel = -1
        else:
            try:
                discordget(f"channels/{guild.verify_log_channel}")
            except (DiscordError, NetworkingError):
                raise LookupError("Unknown log channel")

            log_channel = guild.verify_log_channel

    if log_channel > 0 and highest_id == 0:
        try:
            discordpost.delay(
                endpoint=f"channels/{log_channel}/messages",
                payload={
                    "embeds": [
                        {
                            "title": "Verification Started",
                            "description": inspect.cleandoc(
                                f"""Verification of members of {guild.name} has started <t:{int(time.time())}:R>.

                                API Keys: {len(admin_keys)}
                                Estimated Members: {server_data['approximate_member_count']}"""
                            ),
                            "color": SKYNET_INFO,
                            "timestamp": datetime.datetime.utcnow().isoformat(),
                            "footer": {"text": torn_timestamp()},
                        }
                    ]
                },
            ).forget()
        except (DiscordError, NetworkingError):
            pass

    if (
        int(redis_client.get(f"tornium:verify:{guild.sid}:member_count"))
        > server_data["approximate_member_count"] * 0.99
        or int(redis_client.get(f"tornium:verify:{guild.sid}:member_fetch_runs"))
        >= (server_data["approximate_member_count"] // ((15 * len(admin_keys)) + 1))
        or int(redis_client.get(f"tornium:verify:{guild.sid}:member_fetch_runs")) >= 50
    ):
        if log_channel > 0:
            discordpost.delay(
                endpoint=f"channels/{log_channel}/messages",
                payload={
                    "embeds": [
                        {
                            "title": "Verification Finished",
                            "description": inspect.cleandoc(
                                f"""Verification of members of {guild.name} has finished <t:{int(time.time())}:R>.

                                Estimated Members: {server_data['approximate_member_count']}
                                Members Attempted: {redis_client.get(f'tornium:verify:{guild.sid}:member_count')}
                                Loops Run: {redis_client.get(f'tornium:verify:{guild.sid}:member_fetch_runs')}
                                """
                            ),
                            "color": SKYNET_INFO,
                            "timestamp": datetime.datetime.utcnow().isoformat(),
                            "footer": {"text": torn_timestamp()},
                        }
                    ]
                },
            ).forget()

        return

    try:
        guild_members: list = discordget(
            f"guilds/{guild.sid}/members?limit={15 * len(admin_keys)}&after={highest_id}",
        )
    except DiscordError as e:
        if log_channel > 0:
            discordpost.delay(
                endpoint=f"channels/{log_channel}/messages",
                payload={
                    "embeds": [
                        {
                            "title": "Discord API Error",
                            "description": f'The Discord API has raised error code {e.code}: "{e.message}".',
                            "color": SKYNET_ERROR,
                        }
                    ]
                },
            ).forget()

        raise e
    except NetworkingError as e:
        if log_channel > 0:
            discordpost.delay(
                endpoint=f"channels/{log_channel}/messages",
                payload={
                    "embeds": [
                        {
                            "title": "Discord HTTP Error",
                            "description": f'The Discord API has return an HTTP error {e.code}: "{e.message}".',
                            "color": SKYNET_ERROR,
                        }
                    ]
                },
            ).forget()

        raise e

    redis_client.incrby(f"tornium:verify:{guild_id}:member_count", len(guild_members))
    redis_client.incrby(f"tornium:verify:{guild.sid}:member_fetch_runs", 1)
    counter = 0

    guild_member: dict
    for guild_member in guild_members:
        if "user" not in guild_member:
            continue
        elif guild_member["user"].get("bot") or guild_member["user"].get("system"):
            continue
        elif set(guild_member["roles"]) & set(map(str, guild.exclusion_roles)):  # Exclusion role in member's role
            continue

        counter += 1

        if int(guild_member["user"]["id"]) > highest_id:
            highest_id = int(guild_member["user"]["id"])

        user: typing.Optional[UserModel] = UserModel.objects(discord_id=guild_member["user"]["id"]).first()

        if guild_member.get("nick") in (None, ""):
            nick = guild_member["user"]["username"]
        else:
            nick = guild_member["nick"]

        if user is None or user.discord_id in ("", 0, None) or force:
            tornget.signature(
                kwargs={
                    "endpoint": f"user/{guild_member['user']['id']}?selections=discord,profile",
                    "key": random.choice(admin_keys),
                    "pass_error": True,
                },
                queue="api",
            ).apply_async(
                expires=300,
                countdown=int(1 + 0.1 * counter),
                link=verify_member_sub.signature(
                    kwargs={
                        "member": {
                            "id": int(guild_member["user"]["id"]),
                            "name": nick,
                            "icon": guild_member["user"].get("avatar"),
                            "roles": guild_member["roles"],
                        },
                        "log_channel": log_channel,
                        "guild_id": guild.sid,
                    }
                ),
            )
        else:
            verify_member_sub.signature(
                kwargs={
                    "member": {
                        "id": guild_member["user"]["id"],
                        "name": nick,
                        "icon": guild_member["user"].get("avatar"),
                        "roles": guild_member["roles"],
                    },
                    "log_channel": log_channel,
                    "guild_id": guild.sid,
                    "user_data": {
                        "player_id": user.tid,
                    },
                    "new_data": False,
                }
            ).apply_async(
                expires=300,
                countdown=int(1 + 0.1 * counter),
            )

    verify_users.signature(
        kwargs={
            "guild_id": guild_id,
            "admin_keys": admin_keys,
            "force": force,
            "highest_id": highest_id,
            "log_channel": log_channel,
        }
    ).apply_async(
        countdown=30,
        expires=300,
    ).forget()


@celery.shared_task(name="tasks.guild.verify_member_sub", routing_key="quick.verify_member_sub", queue="quick")
def verify_member_sub(user_data: dict, log_channel: int, member: dict, guild_id: int, new_data=True):
    if "error" in user_data:
        return
    elif user_data["player_id"] == 0:
        return

    if new_data:
        user: UserModel = UserModel.objects(tid=user_data["player_id"]).modify(
            upsert=True,
            new=True,
            set__name=user_data["name"],
            set__level=user_data["level"],
            set__last_refresh=int(time.time()),
            set__discord_id=user_data["discord"]["discordID"] if user_data["discord"]["discordID"] != "" else 0,
            set__factionid=user_data["faction"]["faction_id"],
            set__status=user_data["last_action"]["status"],
            set__last_action=user_data["last_action"]["timestamp"],
        )
    else:
        user: typing.Optional[UserModel] = UserModel.objects(tid=user_data["player_id"]).first()

        if user is None:
            return

    if user.discord_id in (0, None, ""):
        return

    patch_json: dict = {}
    guild: typing.Optional[ServerModel] = ServerModel.objects(sid=guild_id).first()

    if guild is None:
        raise LookupError("Server not found in database")

    if guild.verify_template != "":
        nick = (
            jinja2.Environment(autoescape=True)
            .from_string(guild.verify_template)
            .render(name=user.name, tid=user.tid, tag="")
        )

        if nick != member["name"]:
            patch_json["nick"] = nick

    if len(guild.verified_roles) != 0:
        verified_role: int
        for verified_role in guild.verified_roles:
            if str(verified_role) in member["roles"]:
                continue
            elif patch_json.get("roles") is None:
                patch_json["roles"] = member["roles"]

            patch_json["roles"].append(str(verified_role))

    if (
        user.factionid != 0
        and guild.faction_verify.get(str(user.factionid)) is not None
        and guild.faction_verify[str(user.factionid)].get("roles") is not None
        and len(guild.faction_verify[str(user.factionid)]["roles"]) != 0
        and guild.faction_verify[str(user.factionid)].get("enabled") not in (None, False)
    ):
        faction_role: int
        for faction_role in guild.faction_verify[str(user.factionid)]["roles"]:
            if str(faction_role) in member["roles"]:
                continue
            elif patch_json.get("roles") is None:
                patch_json["roles"] = member["roles"]

            patch_json["roles"].append(str(faction_role))

    for factiontid, verify_data in guild.faction_verify.items():
        for faction_role in verify_data["roles"]:
            if str(faction_role) in member["roles"] and int(factiontid) != user.factionid:
                if patch_json.get("roles") is None:
                    patch_json["roles"] = member["roles"]

                patch_json["roles"].remove(str(faction_role))

    if (
        user.factionid != 0
        and user.faction_position is not None
        and guild.faction_verify.get(str(user.factionid)) is not None
        and guild.faction_verify[str(user.factionid)].get("positions") is not None
        and len(guild.faction_verify[str(user.factionid)]["positions"]) != 0
        and str(user.faction_position) in guild.faction_verify[str(user.factionid)]["positions"].keys()
        and guild.faction_verify[str(user.factionid)].get("enabled") not in (None, False)
    ):
        position_role: int
        for position_role in guild.faction_verify[str(user.factionid)]["positions"][str(user.faction_position)]:
            if str(position_role) in member["roles"]:
                continue
            elif patch_json.get("roles") is None:
                patch_json["roles"] = member["roles"]

            patch_json["roles"].append(str(position_role))

    valid_position_roles = []

    for factiontid, faction_positions_data in guild.faction_verify.items():
        if "positions" not in faction_positions_data:
            continue

        for position_uuid, position_data in faction_positions_data["positions"].items():
            for position_role in position_data:
                if position_role in valid_position_roles:
                    continue
                elif position_role in member["roles"]:
                    if (
                        str(user.faction_position) in faction_positions_data["positions"]
                        and position_role in faction_positions_data["positions"][str(user.faction_position)]
                    ):
                        valid_position_roles.append(position_role)
                        continue
                    elif patch_json.get("roles") is None:
                        patch_json["roles"] = member["roles"]

                    patch_json["roles"].remove(str(position_role))

    if len(patch_json) == 0:
        return
    elif "roles" in patch_json:
        patch_json["roles"] = list(set(patch_json["roles"]))

    discordpatch.delay(
        endpoint=f"guilds/{guild_id}/members/{user.discord_id}",
        payload=patch_json,
        countdown=math.floor(random.uniform(0, 30)),
    ).forget()

    if log_channel > 0:
        payload = {
            "embeds": [
                {
                    "title": "API Verification Attempted",
                    "description": f"<@{member['id']}> is officially verified by Torn. Their roles and nickname "
                    f"have been updated.",
                    "color": SKYNET_INFO,
                    "author": {
                        "name": member["name"],
                        "url": f"https://discord.com/users/{member['id']}",
                    },
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                }
            ]
        }

        if member.get("avatar") is not None:
            payload["embeds"][0]["author"][
                "icon_url"
            ] = f"https://cdn.discordapp.com/avatars/{member['id']}/{member['avatar']}.webp"

        discordpost.delay(
            endpoint=f"channels/{log_channel}/messages",
            payload=payload,
            countdown=math.floor(random.uniform(0, 15)),
        ).forget()
