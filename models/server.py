# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from models.servermodel import ServerModel
import tasks
import utils


class Server:
    def __init__(self, sid):
        """
        Retrieves the server from the database.

        :param sid: Discord server ID
        """

        server = utils.first(ServerModel.objects(sid=sid))
        if server is None:
            guild = tasks.discordget(f"guilds/{sid}")

            server = ServerModel(
                sid=sid,
                name=guild["name"],
                admins=[],
                prefix="?",
                config={"stakeouts": 0, "assists": 0},
                factions=[],
                stakeoutconfig={"category": 0},
                userstakeouts=[],
                factionstakeouts=[],
                assistschannel=0,
                assist_factions=[],
                assist_mod=0,
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

        self.assistschannel = server.assistschannel
        self.assist_factions = server.assist_factions
        self.assist_mod = server.assist_mod
