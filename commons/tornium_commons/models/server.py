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

import operator
import typing
from functools import lru_cache

from peewee import BigIntegerField, BooleanField, IntegerField, TextField
from playhouse.postgres_ext import ArrayField, JSONField

from .base_model import BaseModel


class Server(BaseModel):
    # Basic data
    sid = BigIntegerField(primary_key=True)
    name = TextField()
    admins = ArrayField(IntegerField, default=[], index=False)  # Array of admin user IDs
    icon = TextField(null=True)  # hash of Discord server icon

    # Faction data
    factions = ArrayField(IntegerField, default=[], index=False)  # Array of faction IDs

    # Verification configuration
    verify_enabled = BooleanField(default=False)
    auto_verify_enabled = BooleanField(default=False)
    gateway_verify_enabled = BooleanField(default=False)
    verify_template = TextField(default="{{ name }} [{{ tid }}]")
    verified_roles = ArrayField(BigIntegerField, default=[], index=False)
    exclusion_roles = ArrayField(BigIntegerField, default=[], index=False)
    faction_verify = JSONField(default={})
    verify_log_channel = BigIntegerField(default=0)
    verify_jail_channel = BigIntegerField(default=0)

    # Banking configuration
    banking_config = JSONField(default={})

    # Armory tracking configuration
    # per faction: {
    #     str(faction_id): {
    #         "enabled": bool(false default)
    #         "channel": int(channel_id)
    #         "roles": [list of int(roles)]
    #         "items": {
    #             str(item_id): int(minimum_quantity)
    #         }
    #     }
    # }
    armory_enabled = BooleanField(default=False)
    armory_config = JSONField(default={})

    # OC configuration
    oc_config = JSONField(default={})

    def get_text_channels(
        self,
        discord_get: typing.Callable,
        api=False,
        include_threads=False,
    ):
        def parse(value):
            if api:
                return str(value)
            else:
                return value

        channels_query = discord_get(f"guilds/{self.sid}/channels")
        channels = {"0": {"name": "", "channels": {}, "position": -1}}

        for channel in channels_query:
            if channel["type"] == 4 and channel["id"] not in channels:
                channels[channel["id"]] = {
                    "id": parse(channel["id"]),
                    "name": channel["name"] if "name" in channel else "",
                    "position": channel["position"] if "position" in channel else -1,
                    "channels": {},
                }
            elif channel["type"] == 4 and channel["id"] in channels and channels[channel["id"]]["name"] is None:
                channels[channel["id"]]["name"] = channel["name"]
            elif channel["type"] == 0:
                if "parent_id" not in channel or channel.get("parent_id") is None:
                    channels["0"]["channels"][channel["id"]] = {
                        "id": parse(channel["id"]),
                        "name": channel["name"] if "name" in channel else "",
                        "position": (channel["position"] if "position" in channel else -1),
                    }
                elif channel["parent_id"] in channels:
                    channels[channel["parent_id"]]["channels"][channel["id"]] = {
                        "id": parse(channel["id"]),
                        "name": channel["name"] if "name" in channel else "",
                        "position": (channel["position"] if "position" in channel else -1),
                    }
                else:
                    channels[channel["parent_id"]] = {
                        "id": parse(channel["parent_id"]),
                        "name": None,
                        "channels": {
                            channel["id"]: {
                                "id": parse(channel["id"]),
                                "name": channel["name"] if "name" in channel else "",
                                "position": (channel["position"] if "position" in channel else -1),
                            }
                        },
                        "position": -2,
                    }

            if channel["type"] == 4 and channels[channel["id"]] == -2:
                channels[channel["id"]]["position"] = channel["position"]

        if not include_threads:
            return channels

        threads_query = discord_get(f"guilds/{self.sid}/threads/active")

        # Thread is a channel object
        for thread in threads_query["threads"]:
            if thread["type"] not in [
                11,  # PUBLIC_THREAD
                12,  # PRIVATE_THREAD
            ]:
                continue
            elif thread["thread_metadata"]["locked"]:
                # Locked thread... needs to be unlocked by an admin
                continue
            # Not handling threads that are currently archived as they'll be unarchived if a message is sent in them

            parent_channel_id: str = thread["parent_id"]

            for category_id, category in channels.items():
                if parent_channel_id not in category["channels"]:
                    continue

                parent_channel_obj: dict = category["channels"][parent_channel_id]

                if "threads" not in parent_channel_obj:
                    parent_channel_obj["threads"] = {}

                parent_channel_obj["threads"][thread["id"]] = {
                    "id": parse(thread["id"]),
                    "name": thread.get("name", ""),
                    "position": thread.get("position", -1),
                }
                break

        return channels

    def get_roles(self, discord_get: typing.Callable, api=False):
        def parse(value):
            if api:
                return str(value)
            else:
                return value

        roles_query = discord_get(f"guilds/{self.sid}")
        roles = {}

        for role in roles_query.get("roles"):
            if role["name"] == "@everyone":
                continue
            elif role["managed"]:  # whether this role is managed by an integration
                continue
            elif "tags" in role and ("bot_id" in role["tags"] or "integration_id" in role["tags"]):
                continue

            roles[role["id"]] = {
                "id": parse(role["id"]),
                "name": role["name"],
                "position": role["position"],
            }

        return dict(
            sorted(
                roles.items(),
                key=lambda x: operator.getitem(x[1], "position"),
                reverse=True,
            )
        )

    @staticmethod
    def server_str(sid: int) -> str:
        return f"{Server.server_name(sid)} [{sid}]"

    @staticmethod
    @lru_cache
    def server_name(sid: int) -> str:
        return Server.select(Server.name).where(Server.sid == sid).get().name
