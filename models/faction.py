# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import random

from flask_login import current_user
from mongoengine.queryset.visitor import Q
from honeybadger import honeybadger

from models.factionmodel import FactionModel
from models.server import Server
from models.usermodel import UserModel
import tasks
import utils


class Faction:
    def __init__(self, tid, key=""):
        """
        Retrieves the faction from the database.

        :param tid: Torn faction ID
        :param key: Torn API Key to be utilized (uses current user's key if not passed)
        """

        faction = utils.first(FactionModel.objects(tid=tid))
        if faction is None:
            try:
                faction_data = tasks.tornget(
                    f"faction/{tid}?selections=basic",
                    key if key != "" else current_user.key,
                )
            except utils.TornError as e:
                utils.get_logger().exception(e)
                honeybadger.notify(e, context={"code": e.code, "endpoint": e.endpoint})
                raise e

            now = utils.now()

            faction = FactionModel(
                tid=tid,
                name=faction_data["name"],
                respect=faction_data["respect"],
                capacity=faction_data["capacity"],
                leader=faction_data["leader"],
                coleader=faction_data["co-leader"],
                aa_keys=[],
                last_members=now,
                guild=0,
                config={"vault": 0, "stats": 1},
                vaultconfig={"banking": 0, "banker": 0, "withdrawal": 0},
                statconfig={"global": 0},
                chainconfig={"od": 0, "odchannel": 0},
                chainod={},
                groups=[],
                pro=False,
                pro_expiration=0,
            )

            try:
                tasks.tornget(
                    f"faction/{tid}?selections=positions",
                    key if key != "" else current_user.key,
                )
            except utils.TornError:
                pass

            faction.save()

            for member_id, member_data in faction_data["members"].items():
                user: UserModel = utils.first(UserModel.objects(tid=int(member_id)))

                if user is None:
                    UserModel(
                        tid=int(member_id),
                        name=member_data["name"],
                        level=member_data["level"],
                        last_action=member_data["last_action"]["timestamp"],
                        status=member_data["last_action"]["status"],
                    ).save()
                else:
                    user.name = member_data["name"]
                    user.level = member_data["level"]
                    user.last_action = member_data["last_action"]["timestamp"]
                    user.status = member_data["last_action"]["status"]
                    user.save()

        self.tid = tid
        self.name = faction.name
        self.respect = faction.respect
        self.capacity = faction.capacity
        self.leader = faction.leader
        self.coleader = faction.coleader
        self.aa_keys = faction.aa_keys

        self.last_members = faction.last_members

        self.guild = faction.guild
        self.config = faction.config
        self.vault_config = faction.vaultconfig

        self.stat_config = faction.statconfig

        self.chain_config = faction.chainconfig
        self.chain_od = faction.chainod

        self.groups = faction.groups

        self.pro = faction.pro
        self.pro_expiration = faction.pro_expiration

    def refresh_keys(self):
        users = UserModel.objects(
            Q(factionaa=True) & Q(factionid=self.tid) & Q(key__ne="")
        )
        keys = []

        for user in users:
            if user.key == "":
                continue

            keys.append(user.key)

        keys = list(set(keys))

        faction: FactionModel = utils.first(FactionModel.objects(tid=self.tid))
        faction.aa_keys = keys
        faction.save()
        self.aa_keys = keys

        return keys

    def rand_key(self):
        if len(self.aa_keys) == 0:
            return None
        return random.choice(self.aa_keys)

    def get_config(self):
        if self.guild == 0:
            return {"vault": 0, "stats": 1}

        server = Server(self.guild)
        if self.tid not in server.factions:
            raise Exception  # TODO: Make exception more descriptive

        return self.config

    def refresh(self, key=None, force=False):
        now = utils.now()

        if force or (now - self.last_members) > 1800:
            if key is None:
                key = current_user.key

                if key == "":
                    raise Exception  # TODO: Make exception more descriptive

            try:
                faction_data = tasks.tornget(
                    f"faction/{self.tid}?selections=basic", key
                )
            except utils.TornError as e:
                utils.get_logger().exception(e)
                honeybadger.notify(e, context={"code": e.code, "endpoint": e.endpoint})
                raise e

            faction: FactionModel = utils.first(FactionModel.objects(tid=self.tid))
            faction.name = faction_data["name"]
            faction.respect = faction_data["respect"]
            faction.capacity = faction_data["capacity"]
            faction.leader = faction_data["leader"]
            faction.coleader = faction_data["co-leader"]
            faction.last_members = now
            faction.save()

            for member_id, member_data in faction_data["members"].items():
                user: UserModel = utils.first(UserModel.objects(tid=int(member_id)))

                if user is None:
                    UserModel(
                        tid=int(member_id),
                        name=member_data["name"],
                        level=member_data["level"],
                        last_action=member_data["last_action"]["timestamp"],
                        status=member_data["last_action"]["status"],
                        factionid=self.tid,
                    ).save()
                else:
                    user.name = member_data["name"]
                    user.level = member_data["level"]
                    user.last_action = member_data["last_action"]["timestamp"]
                    user.status = member_data["last_action"]["status"]
                    user.factionid = self.tid
                    user.save()
