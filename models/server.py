# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from models.servermodel import ServerModel
import redisdb
import tasks
import utils
from utils.errors import DiscordError


class Server:
    def __init__(self, sid):
        """
        Retrieves the server from the database.

        :param sid: Discord server ID
        """

        server = ServerModel.objects(sid=sid).first()
        if server is None:
            try:
                guild = tasks.discordget(f"guilds/{sid}")
                skynet = False
            except DiscordError as e:
                if e.code == 10004:
                    guild = tasks.discordget(f"guilds/{sid}", dev=True)
                    skynet = True
                else:
                    raise e

            server = ServerModel(
                sid=sid,
                name=guild["name"],
                admins=[],
                prefix="?",
                config={"stakeouts": 0, "assists": 0, "verify": 0},
                factions=[],
                stakeoutconfig={"category": 0},
                userstakeouts=[],
                factionstakeouts=[],
                faction_verify={},
                verify_log_channel=0,
                welcome_channel=0,
                assistschannel=0,
                assist_factions=[],
                assist_mod=0,
                skynet=skynet,
            )
            server.save()

        self.sid = sid
        self.name = server.name
        self.admins = server.admins
        self.prefix = server.prefix
        self.config = server.config

        self.factions = server.factions

        self.stakeout_config = server.stakeoutconfig
        self.user_stakeouts = server.userstakeouts
        self.faction_stakeouts = server.factionstakeouts

        self.faction_verify = server.faction_verify
        self.verify_log_channel = server.verify_log_channel
        self.welcome_channel = server.welcome_channel

        self.assistschannel = server.assistschannel
        self.assist_factions = server.assist_factions
        self.assist_mod = server.assist_mod

        self.skynet = server.skynet

    def get_text_channels(self):
        channels_query = tasks.discordget(
            f"guilds/{self.sid}/channels", dev=self.skynet
        )
        channels = {0: {"name": "", "channels": {}}}

        for channel in channels_query:
            if channel["type"] == 4 and channel["id"] not in channels:
                channels[channel["id"]] = {
                    "id": channel["id"],
                    "name": channel["name"] if "name" in channel else "",
                    "channels": {},
                }
            elif (
                channel["type"] == 4
                and channel["id"] in channels
                and channels[channel["id"]]["name"] is None
            ):
                channels[channel["id"]]["name"] = channel["name"]
            elif channel["type"] == 0:
                if "parent_id" not in channel or channel.get("parent_id") is None:
                    channels[0]["channels"][channel["id"]] = {
                        "id": channel["id"],
                        "name": channel["name"] if "name" in channel else "",
                    }
                elif channel["parent_id"] in channels:
                    channels[channel["parent_id"]]["channels"][channel["id"]] = {
                        "id": channel["id"],
                        "name": channel["name"] if "name" in channel else "",
                    }
                else:
                    channels[channel["parent_id"]] = {
                        "name": None,
                        "channels": {
                            channel["id"]: {
                                "id": channel["id"],
                                "name": channel["name"] if "name" in channel else "",
                            }
                        },
                    }

        return channels

    def get_roles(self):
        roles_query = tasks.discordget(
            f"guilds/{self.sid}", dev=self.skynet
        )
        roles = {}

        for role in roles_query.get("roles"):
            if role["name"] == "@everyone":
                continue
            elif role["managed"]:  # whether this role is managed by an integration
                continue
            elif "tags" in role and ("bot_id" in role["tags"] or "integration_id" in role["tags"]):
                continue

            roles[role["id"]] = {
                "id": role["id"],
                "name": role["name"],
                "position": role["position"],
            }

        return roles
