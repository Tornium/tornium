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

import jinja2
from peewee import DoesNotExist, Expression
from tornium_commons import rds
from tornium_commons.errors import DiscordError, NetworkingError
from tornium_commons.formatters import torn_timestamp
from tornium_commons.models import FactionPosition, Server, ServerAttackConfig, User
from tornium_commons.skyutils import SKYNET_ERROR, SKYNET_GOOD, SKYNET_INFO

import celery
from celery.utils.log import get_task_logger

from .api import discordget, discordpatch, discordpost
from .user import update_user

logger: logging.Logger = get_task_logger("celery_app")


def refresh_guild(guild: dict):
    admins: typing.Set[int] = set()

    try:
        admins.add(User.select(User.tid).where(User.discord_id == guild["owner_id"]).get().tid)
    except DoesNotExist:
        pass

    members = None
    largest_member_id = 0
    while members is None or len(members) >= 1000:
        if members is None:
            members = discordget(f'guilds/{guild["id"]}/members?limit=1000')
        else:
            members = discordget(f"guilds/{guild['id']}/members?limit=1000&after={largest_member_id}")

        discord_admins: typing.Set[int] = set()

        # TODO: Skip bots
        for member in members:
            largest_member_id = max(largest_member_id, int(member["user"]["id"]))

            for guild_role in guild["roles"]:
                # Checks if the user has the role and the role has the administrator permission
                if (
                    guild_role["id"] in member["roles"]
                    and (int(guild_role["permissions"]) & 0x0000000008) == 0x0000000008
                ):
                    try:
                        discord_admins.add(int(member["user"]["id"]))
                    except DoesNotExist:
                        pass

                    break

        admins.update(set(u.tid for u in User.select(User.tid).where(User.discord_id << discord_admins)))

    Server.update(admins=list(set(admins))).where(Server.sid == guild["id"]).execute()

    try:
        guild_db: Server = Server.select().where(Server.sid == guild["id"]).get()

        for faction_tid, faction_data in guild_db.faction_verify.items():
            if "positions" not in faction_data:
                continue

            positions_to_delete = []

            for position_uuid, position_data in faction_data["positions"].items():
                try:
                    position: FactionPosition = (
                        FactionPosition.select(FactionPosition.faction_tid)
                        .where(FactionPosition.pid == position_uuid)
                        .get()
                    )
                except DoesNotExist:
                    positions_to_delete.append(position_uuid)
                    continue

                if position.faction_tid != int(faction_tid):
                    positions_to_delete.append(position_uuid)

            for position_uuid in positions_to_delete:
                guild_db.faction_verify[faction_tid]["positions"].pop(position_uuid)

        guild_db.save()
    except Exception as e:
        logger.exception(e)


@celery.shared_task(
    name="tasks.guild.refresh_guilds",
    routing_key="default.refresh_guilds",
    queue="default",
    time_limit=1200,
)
def refresh_guilds():
    # Largest guild ID and guild count used for pagination if the number of servers
    # is greater than 200 where the API call limits the returned results
    largest_guild_id = None
    guild_count = None

    # Set of guild IDs that no longer have the bot in the server
    guilds_not_updated = set(server.sid for server in Server.select(Server.sid))

    while guild_count is None or guild_count >= 200:
        guild_count = 0

        if largest_guild_id is None:
            guilds = discordget("users/@me/guilds")
        else:
            guilds = discordget(f"users/@me/guilds?after={largest_guild_id}")

        for guild in guilds:
            guild_count += 1

            if largest_guild_id is None or int(guild["id"]) > largest_guild_id:
                largest_guild_id = int(guild["id"])

            try:
                guilds_not_updated.remove(int(guild["id"]))
            except KeyError:
                pass

            Server.insert(
                sid=guild["id"],
                name=guild["name"],
                icon=guild["icon"],
            ).on_conflict(
                conflict_target=[Server.sid],
                preserve=[Server.name, Server.icon],
            ).execute()

            time.sleep(0.5)

            try:
                refresh_guild(discordget(f"guilds/{guild['id']}"))
            except (DiscordError, NetworkingError, celery.exceptions.Retry):
                continue

    for deleted_guild in guilds_not_updated:
        # Delete certain rows that rely upon the server for the primary key
        try:
            ServerAttackConfig.delete().where(ServerAttackConfig.server == deleted_guild).execute()
            Server.delete().where(Server.sid == deleted_guild).execute()
        except (DoesNotExist, AttributeError):
            pass


@celery.shared_task(
    name="tasks.guild.verify_guilds",
    routing_key="default.verify_guilds",
    queue="default",
    time_limit=600,
)
def verify_guilds():
    def _modulo(lhs, rhs):
        return Expression(lhs, "%%", rhs)

    # This task will run every 15 minutes.
    # Each server will be part of a certain run of the task based on the server ID
    #
    # Seconds since new days: t % 86400
    # Number of 15 minute intervals since new days: previous // 900
    for guild in Server.select(Server.sid).where(
        (Server.verify_enabled == True)
        & (Server.auto_verify_enabled)
        & (_modulo(Server.sid, 96) == (int(time.time()) % 86400 // 900))
    ):
        verify_users.delay(
            guild_id=guild.sid,
            force=True,
        ).forget()


@celery.shared_task(
    name="tasks.guild.verify_users",
    routing_key="default.verify_users",
    queue="default",
    time_limit=600,
)
def verify_users(
    guild_id: int,
    admin_keys: typing.Optional[list] = None,
    force=False,
    highest_id: int = 0,
    log_channel: int = -2,
):
    # Log channel
    # -2: temporarily disabled (to be verified)
    # -1: disabled
    #  n: channel ID

    guild: Server = (
        Server.select(
            Server.name,
            Server.sid,
            Server.verify_enabled,
            Server.verify_template,
            Server.verified_roles,
            Server.faction_verify,
            Server.admins,
            Server.verify_log_channel,
            Server.exclusion_roles,
        )
        .where(Server.sid == guild_id)
        .get()
    )

    if not guild.verify_enabled:
        raise ValueError("Verification not enabled")
    elif guild.verify_template == "" and len(guild.verified_roles) == 0 and len(guild.faction_verify) == 0:
        raise ValueError("Verification will result in no state change")

    redis_client = rds()

    if redis_client.exists(f"tornium:verify:{guild.sid}:lock") and highest_id == 0:
        raise RuntimeError(f"Run in {redis_client.ttl(f'tornium:verify:{guild.sid}:lock')} seconds")

    redis_client.set(f"tornium:verify:{guild.sid}:lock", 1, ex=600, nx=True)

    if admin_keys is None:
        admin_keys = []

        admin: int
        for admin in guild.admins:
            try:
                admin_keys.append(User.select(User.tid).where(User.tid == admin).get().key)
            except DoesNotExist:
                continue

    if len(admin_keys) == 0:
        raise ValueError("No admin keys are available to use")

    server_data = discordget(
        f"guilds/{guild.sid}?with_counts=true",
    )

    redis_client.set(f"tornium:verify:{guild.sid}:member_count", 0, ex=600, nx=True)
    redis_client.set(f"tornium:verify:{guild.sid}:member_fetch_runs", 0, ex=600, nx=True)
    redis_client.set(f"tornium:verify:{guild.sid}:errors", 0, ex=600, nx=True)

    if log_channel == -2:
        if guild.verify_log_channel == 0 or guild.verify_log_channel is None:
            redis_client.set(f"tornium:verify:{guild.sid}:log_channel", -1, ex=600)
            log_channel = -1
        else:
            try:
                discordget(f"channels/{guild.verify_log_channel}")
            except (DiscordError, NetworkingError) as e:
                raise LookupError(f"Unknown log channel: {e}")

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
            f"guilds/{guild.sid}/members?limit={25 * len(admin_keys)}&after={highest_id}",
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
                channel=log_channel,
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
                channel=log_channel,
            ).forget()

        raise e

    redis_client.incrby(f"tornium:verify:{guild.sid}:member_count", len(guild_members))
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

        user: typing.Optional[User] = (
            User.select(User.discord_id, User.tid, User.last_refresh)
            .where(User.discord_id == guild_member["user"]["id"])
            .first()
        )

        if guild_member.get("nick") in (None, ""):
            nick = guild_member["user"]["username"]
        else:
            nick = guild_member["nick"]

        kwargs = {}

        if counter >= 10:
            kwargs["countdown"] = int(0.1 * counter)

        if (
            user is None
            or user.discord_id in (0, None)
            or (datetime.datetime.utcnow() - user.last_refresh).total_seconds() >= 604800  # One week
            or force
        ):
            update_user.signature(
                kwargs={
                    "key": random.choice(admin_keys),  # TODO: replace this with key rotation via counter
                    "discordid": guild_member["user"]["id"],
                },
                queue="default",
            ).apply_async(
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
                        "gateway": False,
                    },
                    immutable=True,
                ),
                expires=300,
                **kwargs,
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
                    "gateway": False,
                }
            ).apply_async(
                expires=300,
                **kwargs,
            )

    verify_users.signature(
        kwargs={
            "guild_id": guild.sid,
            "admin_keys": admin_keys,
            "force": force,
            "highest_id": highest_id,
            "log_channel": log_channel,
        }
    ).apply_async(
        countdown=60,
        expires=300,
    ).forget()


def member_verification_name(
    name: str, tid: int, tag: str, name_template: str = "{{ name }} [{{ tid }}]"
) -> typing.Optional[str]:
    if name_template == "":
        return None

    return (
        jinja2.Environment(autoescape=True)
        .from_string(name_template)
        .render(
            name=name,
            tid=tid,
            tag=tag,
        )
    )


def member_verified_roles(verified_roles: typing.List[int]) -> typing.Set[str]:
    return set(str(role) for role in verified_roles)


def member_faction_roles(faction_verify: dict, faction_id: int) -> typing.Set[str]:
    if faction_id in (0, None):
        return set()
    elif faction_verify.get(str(faction_id)) is None:
        return set()
    elif len(faction_verify[str(faction_id)].get("roles", [])) == 0:
        return set()
    elif not faction_verify[str(faction_id)].get("enabled"):
        return set()

    return set(str(role) for role in faction_verify[str(faction_id)]["roles"])


def invalid_member_faction_roles(faction_verify: dict, faction_id: int) -> typing.Tuple[str]:
    roles = set()

    faction_id: int
    verify_data: dict
    for verify_faction_id, verify_data in faction_verify.items():
        if int(verify_faction_id) == faction_id:
            continue

        roles.update(set(str(role) for role in verify_data.get("roles", tuple())))

    return roles


def member_position_roles(
    faction_verify: dict, faction_id: int, position: typing.Optional[FactionPosition]
) -> typing.Set[str]:
    if faction_id in (0, None):
        return set()
    elif position is None:
        return set()
    elif faction_verify.get(str(faction_id)) is None:
        return set()
    elif not faction_verify[str(faction_id)].get("enabled"):
        return set()
    elif str(position.pid) not in faction_verify[str(faction_id)].get("positions", {}):
        return set()

    return set(str(role) for role in faction_verify[str(faction_id)]["positions"][str(position.pid)])


def invalid_member_position_roles(
    faction_verify: dict, faction_id: int, position: typing.Optional[FactionPosition]
) -> typing.Set[str]:
    # All position roles are invalid for leader, co-leader, and recruits

    roles = set()

    for verify_faction_id, faction_positions_data in faction_verify.items():
        if int(verify_faction_id) == faction_id:
            continue

        for position_uuid, position_roles in faction_positions_data.get("positions", {}).items():
            if position is not None and position_uuid == str(position.pid):
                continue

            roles.update(set(str(role) for role in position_roles))

    return roles


@celery.shared_task(
    name="tasks.guild.verify_member_sub",
    routing_key="quick.verify_member_sub",
    queue="quick",
    time_limit=60,
)
def verify_member_sub(log_channel: int, member: dict, guild_id: int, gateway: bool = False):
    # TODO: Cache guild verification config so the same database calls aren't made for every user
    guild: Server = Server.select().where(Server.sid == guild_id).get()

    try:
        user: User = User.select().where(User.discord_id == member["id"]).get()
    except DoesNotExist:
        if log_channel <= 0:
            return

        discordpost.delay(
            endpoint=f"channels/{log_channel}/messages",
            payload={
                "embeds": [
                    {
                        "title": "API Verification Failed",
                        "description": f"<@{member['id']}> is not found in the database and is most likely not verified by Torn.",
                        "color": SKYNET_ERROR,
                    }
                ],
            },
            countdown=math.floor(random.uniform(0, 15)),
        ).forget()

        if gateway and guild.verify_jail_channel != 0:
            discordpost.delay(
                endpoint=f"channels/{guild.verify_jail_channel}/messages",
                payload={
                    "content": f"<@{member['id']}>",
                    "embeds": [
                        {
                            "title": "API Verification Failed",
                            "description": f"<@{member['id']}> could not be found in the database. This is typically caused by failed verification. Please make sure that you've been officially verified through Torn. Once you're verified, you can reverify with the `/verify` command.",
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "components": [
                        {
                            "type": 1,
                            "components": [
                                {
                                    "type": 2,
                                    "style": 5,
                                    "label": "Official Discord Server",
                                    "url": "https://www.torn.com/discord",
                                }
                            ],
                        }
                    ],
                },
            )

        return

    # Roles will always be strings in this task

    patch_json: dict = {
        "nick": member_verification_name(
            name=user.name,
            tid=user.tid,
            tag=user.faction.tag if user.faction is not None else "",
            name_template=guild.verify_template,
        ),
        "roles": set(str(role) for role in member["roles"]),
    }

    patch_json["roles"] -= invalid_member_faction_roles(
        faction_verify=guild.faction_verify,
        faction_id=user.faction_id,
    )
    patch_json["roles"] -= invalid_member_position_roles(
        faction_verify=guild.faction_verify,
        faction_id=user.faction_id,
        position=user.faction_position,
    )

    patch_json["roles"].update(member_verified_roles(verified_roles=guild.verified_roles))
    patch_json["roles"].update(member_faction_roles(faction_verify=guild.faction_verify, faction_id=user.faction_id))
    patch_json["roles"].update(
        member_position_roles(
            faction_verify=guild.faction_verify,
            faction_id=user.faction_id,
            position=user.faction_position,
        )
    )

    if patch_json["nick"] == member["name"]:
        patch_json.pop("nick")

    if patch_json["roles"] == set(member["roles"]):
        patch_json.pop("roles")
    else:
        patch_json["roles"] = list(patch_json["roles"])

    if len(patch_json) == 0:
        return

    discordpatch.delay(
        endpoint=f"guilds/{guild_id}/members/{user.discord_id}",
        payload=patch_json,
        countdown=math.floor(random.uniform(0, 30)),
    ).forget()

    if gateway and guild.verify_jail_channel != 0:
        payload = {
            "content": f"<@{member['id']}>",
            "embeds": [
                {
                    "title": "Verification Complete",
                    "description": f"Welcome to {guild.name}, <@{member['id']}>. Your verification should now be complete. Contact server administrators if you are having any issues with verification.",
                    "color": SKYNET_GOOD,
                }
            ],
        }

        discordpost.delay(endpoint=f"channels/{guild.verify_jail_channel}/messages", payload=payload).forget()

    if log_channel > 0:
        roles_added = set(patch_json["roles"]) - set(member["roles"]) if "roles" in patch_json else set()
        roles_removed = set(member["roles"]) - set(patch_json["roles"]) if "roles" in patch_json else set()

        payload = {
            "embeds": [
                {
                    "title": "API Verification Attempted",
                    "description": f"<@{member['id']}> is officially verified by Torn. Their roles and nickname "
                    f"are being updated.",
                    "fields": [
                        {
                            "name": "Nickname",
                            "value": (
                                f"{member['name']} -> {patch_json['nick']}" if "nick" in patch_json else "Unchanged"
                            ),
                        },
                        {
                            "name": "Roles Added",
                            "value": (
                                " ".join(tuple(f"<@&{role_id}>" for role_id in roles_added))
                                if len(roles_added) != 0
                                else "None"
                            ),
                        },
                        {
                            "name": "Roles Removed",
                            "value": (
                                " ".join(tuple(f"<@&{role_id}>" for role_id in roles_removed))
                                if len(roles_removed) != 0
                                else "None"
                            ),
                        },
                    ],
                    "color": SKYNET_INFO,
                    "author": {
                        "name": member["name"],
                        "url": f"https://discord.com/users/{member['id']}",
                    },
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                }
            ]
        }

        discordpost.delay(
            endpoint=f"channels/{log_channel}/messages",
            payload=payload,
            countdown=math.floor(random.uniform(0, 15)),
        ).forget()
