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

from tornium_celery.tasks.api import discordget
from tornium_commons.models import ServerModel


class Server:
    def __init__(self, sid):
        """
        Retrieves the server from the database.

        :param sid: Discord server ID
        """

        server = ServerModel.objects(sid=sid).first()
        if server is None:
            raise LookupError("Server not found in the DB")

        self.sid = sid
        self.name = server.name
        self.admins = server.admins
        self.config = server.config
        self.icon = server.icon

        self.factions = server.factions

        self.verify_template = server.verify_template
        self.verified_roles = server.verified_roles
        self.faction_verify = server.faction_verify
        self.verify_log_channel = server.verify_log_channel

        self.retal_config = server.retal_config

        self.banking_config = server.banking_config

        self.assistschannel = server.assistschannel
        self.assist_factions = server.assist_factions

        self.oc_config = server.oc_config

        self.stocks_channel = server.stocks_channel
        self.stocks_config = server.stocks_config

    def get_text_channels(self, include_threads=False, api=False):
        def parse(value):
            if api:
                return str(value)
            else:
                return value

        channels_query = discordget(f"guilds/{self.sid}/channels")
        channels = {"0": {"name": "", "channels": {}, "position": -1}}

        for channel in channels_query:
            if channel["type"] == 4 and channel["id"] not in channels:
                channels[channel["id"]] = {
                    "id": parse(channel["id"]),
                    "name": channel.get("name", ""),
                    "position": channel.get("position", -1),
                    "channels": {},
                }
            elif channel["type"] == 4 and channel["id"] in channels and channels[channel["id"]]["name"] is None:
                channels[channel["id"]]["name"] = channel["name"]
            elif channel["type"] == 0:
                if "parent_id" not in channel or channel.get("parent_id") is None:
                    channels["0"]["channels"][channel["id"]] = {
                        "id": parse(channel["id"]),
                        "name": channel.get("name", ""),
                        "position": channel.get("position", -1),
                    }
                elif channel["parent_id"] in channels:
                    channels[channel["parent_id"]]["channels"][channel["id"]] = {
                        "id": parse(channel["id"]),
                        "name": channel.get("name", ""),
                        "position": channel.get("position", -1),
                    }
                else:
                    channels[channel["parent_id"]] = {
                        "id": parse(channel["parent_id"]),
                        "name": None,
                        "channels": {
                            channel["id"]: {
                                "id": parse(channel["id"]),
                                "name": channel.get("name", ""),
                                "position": channel.get("position", -1),
                            }
                        },
                        "position": -2,
                    }

            if channel["type"] == 4 and channels[channel["id"]] == -2:
                channels[channel["id"]]["position"] = channel["position"]

        if not include_threads:
            return channels

        threads_query = discordget(f"guilds/{self.sid}/threads/active")

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

    def get_roles(self, api=False):
        def parse(value):
            if api:
                return str(value)
            else:
                return value

        roles_query = discordget(f"guilds/{self.sid}")
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
