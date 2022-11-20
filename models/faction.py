# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import random

from flask_login import current_user
from mongoengine.queryset.visitor import Q
from honeybadger import honeybadger

from models.factionmodel import FactionModel
from models.positionmodel import PositionModel
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

        faction = FactionModel.objects(tid=tid).first()
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
                tid=faction_data["ID"],
                name=faction_data["name"],
                respect=faction_data["respect"],
                capacity=faction_data["capacity"],
                leader=faction_data["leader"],
                coleader=faction_data["co-leader"],
                aa_keys=[],
                last_attacks=0,
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
                UserModel.objects(tid=int(member_id)).modify(
                    upsert=True,
                    new=True,
                    set__name=member_data["name"],
                    set__level=member_data["level"],
                    set__last_action=member_data["last_action"]["timestamp"],
                    set__status=member_data["last_action"]["status"],
                )

        self.tid = tid
        self.name = faction.name
        self.respect = faction.respect
        self.capacity = faction.capacity
        self.leader = faction.leader
        self.coleader = faction.coleader
        self.aa_keys = faction.aa_keys

        self.last_members = faction.last_members
        self.last_attacks = faction.last_attacks

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
        keys = []

        position: PositionModel
        for position in PositionModel.objects(
            Q(factiontid=self.tid) & Q(canAccessFactionApi=True)
        ):
            users = UserModel.objects(
                Q(faction_position=position.pid)
                & Q(factionid=self.tid)
                & Q(key__exists=True)
                & Q(key__ne="")
            )

            for user in users:
                if user.key == "":
                    continue

                keys.append(user.key)

            keys = list(set(keys))

        faction: FactionModel = FactionModel.objects(tid=self.tid).first()
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

            faction: FactionModel = FactionModel.objects(tid=self.tid).first()
            faction.name = faction_data["name"]
            faction.respect = faction_data["respect"]
            faction.capacity = faction_data["capacity"]
            faction.leader = faction_data["leader"]
            faction.coleader = faction_data["co-leader"]
            faction.last_members = now
            faction.save()

            for member_id, member_data in faction_data["members"].items():
                if member_data["position"] == "Recruit":
                    position_pid = None
                    faction_aa = False
                elif member_data["position"] in ("Leader", "Co-leader"):
                    position_pid = None
                    faction_aa = True
                else:
                    position: PositionModel = PositionModel.objects(
                        Q(name=member_data["position"])
                        & Q(factiontid=faction_data["ID"])
                    ).first()

                    if position is None:
                        position_pid = None
                        faction_aa = False
                    else:
                        position_pid = position.pid
                        faction_aa = position.canAccessFactionApi

                UserModel.objects(tid=int(member_id)).modify(
                    upsert=True,
                    new=True,
                    set__name=member_data["name"],
                    set__level=member_data["level"],
                    set__last_action=member_data["last_action"]["timestamp"],
                    set__status=member_data["last_action"]["status"],
                    set__factionid=faction_data["ID"],
                    set__faction_position=position_pid,
                    set__faction_aa=faction_aa,
                )
