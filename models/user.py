# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import math

from flask_login import UserMixin, current_user
from honeybadger import honeybadger

from models.usermodel import UserModel
import tasks
import utils


class User(UserMixin):
    def __init__(self, tid, key="", access=3):
        """
        Retrieves the user from the database.

        :param tid: Torn user ID
        """

        user = UserModel.objects(_id=tid).first()
        if user is None:
            user = UserModel(
                tid=tid
            )
            user.save()

        self.tid = tid
        self.name = user.name
        self.level = user.level
        self.last_refresh = user.last_refresh
        self.admin = user.admin
        self.key = user.key
        self.battlescore = user.battlescore
        self.battlescore_update = user.battlescore_update
        self.strength = user.strength
        self.defense = user.defense
        self.speed = user.speed
        self.dexterity = user.dexterity

        self.discord_id = user.discord_id
        self.servers = user.servers

        self.factiontid = user.factionid
        self.aa = user.factionaa
        self.recruiter = user.recruiter
        self.recruiter_code = user.recruiter_code
        self.recruiter_mail_update = user.recruit_mail_update
        self.chain_hits = user.chain_hits

        self.status = user.status
        self.last_action = user.last_action

        self.pro = user.pro
        self.pro_expiration = user.pro_expiration

    def refresh(self, key=None, force=False):
        now = utils.now()

        if force or (now - self.last_refresh) > 1800:
            if self.key != "":
                key = self.key
            elif key is None:  # TODO: Check if there is a session/current_user
                key = current_user.key
                if key == "":
                    raise utils.MissingKeyError

            try:
                if key == self.key:
                    user_data = tasks.tornget(
                        f"user/?selections=profile,battlestats,discord", key
                    )
                else:
                    user_data = tasks.tornget(
                        f"user/{self.tid}?selections=profile,discord", key
                    )
            except utils.TornError as e:
                utils.get_logger().exception(e)
                honeybadger.notify(e, context={"code": e.code, "endpoint": e.endpoint})
                raise e

            user = UserModel.objects(tid=user_data["player_id"]).first()
            user.factionid = user_data["faction"]["faction_id"]
            user.name = user_data["name"]
            user.last_refresh = now
            user.status = user_data["last_action"]["status"]
            user.last_action = user_data["last_action"]["timestamp"]
            user.level = user_data["level"]
            user.discord_id = (
                user_data["discord"]["discordID"]
                if user_data["discord"]["discordID"] != ""
                else 0
            )

            if key == self.key:
                user.battlescore = (
                    math.sqrt(user_data["strength"])
                    + math.sqrt(user_data["speed"])
                    + math.sqrt(user_data["speed"])
                    + math.sqrt(user_data["dexterity"])
                )
                user.battlescore_update = now

            user.save()

            self.name = user_data["name"]
            self.factiontid = user_data["faction"]["faction_id"]
            self.last_refresh = now
            self.status = user_data["last_action"]["status"]
            self.last_action = user_data["last_action"]["timestamp"]
            self.level = user_data["level"]
            self.battlescore = user.battlescore
            self.battlescore_update = now
            self.discord_id = user.discord_id

        return self

    def faction_refresh(self):
        user = UserModel.objects(tid=self.tid).first()

        try:
            tasks.tornget(f"faction/?selections=positions", self.key)
        except:
            self.aa = False
            user.factionaa = False
            return

        self.aa = True
        user.factionaa = True

        user.save()

    def get_id(self):
        return self.tid

    def is_aa(self):
        return self.aa

    def set_key(self, key: str):
        user = UserModel.objects(tid=self.tid).first()
        user.key = key
        self.key = key
        user.save()
