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

import celery
from peewee import DoesNotExist
from tornium_commons import rds
from tornium_commons.models import TornKey, User


@celery.shared_task(
    name="tasks.misc.send_dm",
    routing_key="default.send_dm",
    queue="default",
    time_limit=5,
)
def send_dm(discord_id: int, payload: dict):
    from .api import discordpost

    try:
        channel_id = int(rds().get(f"tornium:discord:dm:{discord_id}"))
    except TypeError:
        dm_channel = discordpost(
            "users/@me/channels",
            payload={
                "recipient_id": discord_id,
            },
        )

        channel_id = dm_channel["id"]
        rds().set(f"tornium:discord:dm:{discord_id}", channel_id, nx=True, ex=86400)

    return discordpost.delay(endpoint=f"channels/{channel_id}/messages", payload=payload)


@celery.shared_task(
    name="tasks.misc.remove_key_error",
    routing_key="quick.remove_key_error",
    queue="quick",
    time_limit=5,
)
def remove_key_error(key: str, error: int):
    try:
        key: TornKey = TornKey.select(TornKey.user).where(TornKey.api_key == key).get()
    except DoesNotExist:
        return

    user_id = key.user_id
    key.delete_instance()

    if error == 7:
        User.update(faction_aa=False, faction_position=None).where(User.tid == user_id).execute()


# TODO: Rewrite this section to be more efficient
# @celery.shared_task(name="tasks.misc.remove_unknown_channel", routing_key="quick.remove_unknown_channel", queue="quick")
# def remove_unknown_channel(channel_id: int):
#     channel_id = int(channel_id)
#
#     faction_od_channel: QuerySet = FactionModel.objects(od_channel=channel_id)
#
#     notifications: QuerySet = NotificationModel.objects(target=channel_id)
#
#     server_verify_channel: typing.Optional[ServerModel] = ServerModel.objects(verify_log_channel=channel_id).first()
#     server_assist_channel: typing.Optional[ServerModel] = ServerModel.objects(assistschannel=channel_id).first()
#     server_feed_channel: typing.Optional[ServerModel] = ServerModel.objects(stocks_channel=channel_id).first()
#
#     faction: FactionModel
#     for faction in faction_od_channel:
#         faction.chainod["odchannel"] = 0
#         faction.save()
#
#     if notifications.count() > 0:
#         notifications.delete()
#
#     if server_verify_channel is not None:
#         server_verify_channel.verify_log_channel = 0
#         server_verify_channel.save()
#
#     if server_assist_channel is not None:
#         server_assist_channel.assistschannel = 0
#         server_assist_channel.save()
#
#     if server_feed_channel is not None:
#         server_feed_channel.stocks_channel = 0
#         server_feed_channel.save()
#
#     server: ServerModel
#     for server in ServerModel.objects():
#         for faction_id, faction_oc in server.oc_config.copy().items():
#             if int(faction_oc["ready"]["channel"]) == channel_id:
#                 server.oc_config[faction_id]["ready"]["channel"] = 0
#             if int(faction_oc["delay"]["channel"]) == channel_id:
#                 server.oc_config[faction_id]["delay"]["channel"] = 0
#
#         for faction_id, faction_retal in server.retal_config.copy().items():
#             if int(faction_retal["channel"]) == channel_id:
#                 server.retal_config[faction_id]["channel"] = 0
#
#         for faction_id, faction_banking in server.banking_config.copy().items():
#             if int(faction_banking["channel"]) == channel_id:
#                 server.banking_config[faction_id]["channel"] = 0
#
#         server.save()
#
#
