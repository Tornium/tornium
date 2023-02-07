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

import logging
import typing

from mongoengine.queryset import QuerySet

from models.factionmodel import FactionModel
from models.factionstakeoutmodel import FactionStakeoutModel
from models.notificationmodel import NotificationModel
from models.servermodel import ServerModel
from models.userstakeoutmodel import UserStakeoutModel
from tasks import celery_app

logger: logging.Logger


@celery_app.task
def remove_unknown_channel(channel_id: int):
    channel_id = int(channel_id)

    faction_vault_channel: QuerySet = FactionModel.objects(vaultconfig__banking=channel_id)
    faction_od_channel: QuerySet = FactionModel.objects(chainconfig__odchannel=channel_id)

    notifications: QuerySet = NotificationModel.objects(target=channel_id)

    server_verify_channel: typing.Optional[ServerModel] = ServerModel.objects(verify_log_channel=channel_id).first()
    server_assist_channel: typing.Optional[ServerModel] = ServerModel.objects(assistschannel=channel_id).first()

    faction: FactionModel
    for faction in faction_vault_channel:
        faction.vaultconfig["banking"] = 0
        faction.save()

    faction: FactionModel
    for faction in faction_od_channel:
        faction.chainod["odchannel"] = 0
        faction.save()

    if notifications.count() > 0:
        notifications.delete()

    if server_verify_channel is not None:
        server_verify_channel.verify_log_channel = 0
        server_verify_channel.save()

    if server_assist_channel is not None:
        server_assist_channel.assistschannel = 0
        server_assist_channel.save()

    faction_stakeout: FactionStakeoutModel
    for faction_stakeout in FactionStakeoutModel.objects():
        for guild, guild_stakeout in faction_stakeout.guilds.items():
            if guild_stakeout.get("channel") in (None, 0, channel_id):
                faction_stakeout.guilds.pop(guild, None)

        if len(faction_stakeout.guilds) == 0:
            faction_stakeout.delete()
        else:
            faction_stakeout.save()

    user_stakeout: UserStakeoutModel
    for user_stakeout in UserStakeoutModel.objects():
        for guild, guild_stakeout in user_stakeout.guilds.items():
            if guild_stakeout.get("channel") in (None, 0, channel_id):
                user_stakeout.guilds.pop(guild, None)

        if len(user_stakeout.guilds) == 0:
            user_stakeout.delete()
        else:
            user_stakeout.save()

    server: ServerModel
    for server in ServerModel.objects():
        for faction_id, faction_oc in server.oc_config.items():
            if int(faction_oc["ready"]["channel"]) == channel_id:
                server.oc_config[faction_id]["ready"]["channel"] = 0
            if int(faction_oc["delay"]["channel"]) == channel_id:
                server.oc_config[faction_id]["delay"]["channel"] = 0

        server.save()


@celery_app.task
def remove_unknown_role(role_id: int):
    role_id = int(role_id)

    faction_vault_role: QuerySet = FactionModel.objects(vaultconfig__banker=role_id)

    server_verify_roles: typing.Optional[ServerModel] = ServerModel.objects(verified_roles=role_id).first()

    faction: FactionModel
    for faction in faction_vault_role:
        faction.vaultconfig["banker"] = 0
        faction.save()

    server: ServerModel
    for server in server_verify_roles:
        server.verified_roles.remove(role_id)
        server.save()

    server: ServerModel
    for server in ServerModel.objects():
        for faction_id, faction_verify in server.faction_verify.items():
            if role_id in faction_verify["roles"]:
                server.faction_verify[faction_id]["roles"].remove(role_id)

        for faction_id, faction_oc in server.oc_config.items():
            if str(role_id) in faction_oc["ready"]["roles"]:
                server.oc_config[faction_id]["ready"]["roles"].remove(str(role_id))
            if str(role_id) in faction_oc["delay"]["roles"]:
                server.oc_config[faction_id]["delay"]["roles"].remove(str(role_id))

        server.save()
