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
import typing

from peewee import DoesNotExist
from tornium_commons.formatters import commas, find_list
from tornium_commons.models import Item, Notification, Server, User
from tornium_commons.skyutils import SKYNET_ERROR, SKYNET_GOOD, SKYNET_INFO

_NOTIF_TYPE_MAP = {
    "percent": "percent below market value",
    "price": "below specified price",
    "quantity": "above specified quantity",
}


def item_notif_init(interaction, user: User, item: Item, subcommand_data, *args, **kwargs):
    notif_type = find_list(subcommand_data, "name", "type")
    value = find_list(subcommand_data, "name", "value")
    channel = find_list(subcommand_data, "name", "channel")
    persistence = find_list(subcommand_data, "name", "persistent")

    if notif_type == -1 or notif_type[1]["value"] not in [
        "percent",
        "price",
        "quantity",
    ]:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Invalid Notification Type",
                        "description": "The item notification type that was passed was invalid.",
                        "color": SKYNET_ERROR,
                    },
                ],
                "flags": 64,
            },
        }

    notif_type = notif_type[1]["value"]
    value = value[1]["value"]

    if channel == -1:
        channel = None
        private = True
    else:
        channel = channel[1]["value"]
        private = False

    if persistence == -1:
        persistence = False
    else:
        persistence = persistence[1]["value"]

    if private and user.discord_id == 0:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Verification Required",
                        "description": "Verification is required for private notifications.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }
    elif not private and ("member" not in interaction or "guild_id" not in interaction):
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Illegal Command Input",
                        "description": "The command must be run in a server for a channel to be passed.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }

    if private:
        if (
            Notification.select()
            .where(
                (Notification.n_type == 3) & (Notification.recipient_guild == 0) & (Notification.invoker == user.tid)
            )
            .count()
            > 10
        ):
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Too Many Notifications",
                            "description": "You have too many item notifications. To prevent service performance "
                            "degradation, at this time, there is a maximum of 10 item notifications per user in DMs.",
                            "color": SKYNET_ERROR,
                        },
                    ],
                    "flags": 64,
                },
            }
    else:
        try:
            guild: Server = Server.get_by_id(interaction["guild_id"])
        except DoesNotExist:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Server Not Located",
                            "description": "This server could not be located in Tornium's database.",
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,
                },
            }

        if user.tid not in guild.admins:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Permission Denied",
                            "description": "You must be a server admin to run this command in this server. Please "
                            "try in another server where you admin or in a DM.",
                            "color": SKYNET_ERROR,
                        }
                    ],
                    "flags": 64,
                },
            }

        n_count = (
            Notification.select()
            .where((Notification.n_type == 3) & (Notification.recipient_guild == guild.sid))
            .count()
        )

        if n_count > 35:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Too Many Notifications",
                            "description": "You have too many item notifications. To prevent service performance "
                            "degradation, at this time, there is a maximum of 35 item notifications per server.",
                            "color": SKYNET_ERROR,
                        },
                    ],
                    "flags": 64,
                },
            }
        elif n_count > len(guild.admins) * 10:
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Too Many Notifications",
                            "description": "You have too many item notifications. To prevent API key overuse, there is "
                            "a maximum of 10 calls per server admin.",
                            "color": SKYNET_ERROR,
                        },
                    ],
                    "flags": 64,
                },
            }

    notification = Notification.create(
        invoker=user.tid,
        time_created=datetime.datetime.utcnow(),
        recipient=user.discord_id if private else channel,
        recipient_guild=0 if private else int(interaction["guild_id"]),
        n_type=3,
        target=item.tid,
        persistent=persistence,
        enabled=False,
        options={
            "type": notif_type,
            "value": value,
        },
    )

    return {
        "type": 4,
        "data": {
            "embeds": [
                {
                    "title": "Notification Created",
                    "description": f"A item notification has been created for {item.name} with the following "
                    f"configuration.",
                    "fields": [
                        {
                            "name": "Item",
                            "value": f"{item.name} [{item.tid}]",
                            "inline": True,
                        },
                        {
                            "name": "Notification Type",
                            "value": _NOTIF_TYPE_MAP[notif_type].capitalize(),
                        },
                        {
                            "name": "Private",
                            "value": private,
                            "inline": True,
                        },
                        {
                            "name": "Target Channel",
                            "value": "Direct Message" if private else f"<#{notification.recipient}>",
                            "inline": True,
                        },
                    ],
                    "footer": {
                        "text": f"DB ID: {notification.get_id()}",
                    },
                    "color": SKYNET_GOOD,
                },
            ],
            "components": [
                {
                    "type": 1,
                    "components": [
                        {
                            "type": 2,
                            "style": 3,
                            "label": "Enable Notification",
                            "custom_id": f"notify:items:{notification.get_id()}:enable",
                        },
                        {
                            "type": 2,
                            "style": 4,
                            "label": "Delete Notification",
                            "custom_id": f"notify:items:{notification.get_id()}:delete",
                        },
                    ],
                },
            ],
        },
    }


def list_item_notifs(interaction, user: User, *args, **kwargs):
    if "guild_id" in interaction:
        notifications = Notification.select().where(
            (Notification.n_type == 3)
            & (
                (Notification.recipient_guild == int(interaction["guild_id"]))
                | ((Notification.recipient_guild == 0) & (Notification.invoker == user.tid))
            )
        )
    else:
        notifications = Notification.select().where(
            (Notification.n_type == 3) & (Notification.recipient_guild == 0) & (Notification.invoker == user.tid)
        )

    if notifications.count() == 0:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "No Notifications Found",
                        "description": "No item notifications were located in the database.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flag": 64,
            },
        }

    payload = {
        "type": 4,
        "data": {
            "embeds": [
                {
                    "title": "List of Item Notifications",
                    "description": f"{notifications.count()} notifications located...\n",
                    "color": SKYNET_INFO,
                }
            ]
        },
    }

    notification: Notification
    for notification in notifications:
        if notification.recipient_guild == 0:
            recipient = "Direct Message"
        else:
            recipient = f"<#{notification.recipient}>"

        if notification.options.get("type") == "percent":
            value = f"{notification.options['value']}% below market value of"
        elif notification.options.get("type") == "price":
            value = f"Below ${commas(int(notification.options['value']))} for"
        elif notification.options.get("type") == "quantity":
            value = f"Above {commas(int(notification.options['value']))}x of"
        else:
            value = "ERROR"

        payload["data"]["embeds"][0]["description"] += f"\n{value} {Item.item_str(notification.target)} - {recipient}"

    return payload


def _generate_item_info_payload(
    notification: Notification,
    item: Item,
    current_number,
    total_count,
    previous_notif: typing.Optional[Notification] = None,
    next_notif: typing.Optional[Notification] = None,
) -> dict:
    notification_description = "This notification will trigger when "

    if notification.options["type"] == "percent":
        notification_description += (
            f"{item.name} can be found on the market for {notification.options['value']}% below market value."
        )
    elif notification.options["type"] == "price":
        notification_description += (
            f"{item.name} can be found on the market for less than ${commas(int(notification.options['value']))}."
        )
    elif notification.options["type"] == "quantity":
        notification_description += (
            f"more than {commas(int(notification.options['value']))}x of {item.name} can be found on the market."
        )
    else:
        notification_description = "ERROR"

    enabled = notification.enabled
    payload = {
        "embeds": [
            {
                "title": f"Item Notification: {item.name}",
                "description": f"Showing item notification information for {item.name} [{item.tid}]\n\n{notification_description}:",
                "fields": [
                    {
                        "name": "Time Created",
                        "value": f"<t:{int(notification.time_created.timestamp())}:f>",
                        "inline": True,
                    },
                    {
                        "name": "Recipient",
                        "value": "Direct Message"
                        if notification.recipient_guild == 0
                        else f"<#{notification.recipient}>",
                        "inline": True,
                    },
                    {
                        "name": "Persistent",
                        "value": str(notification.persistent),
                        "inline": True,
                    },
                ],
                "footer": {"text": f"DB ID: {notification.get_id()} | Showing {current_number}/{total_count}..."},
            }
        ],
        "components": [
            {
                "type": 1,
                "components": [
                    {
                        "type": 2,
                        "style": 4 if enabled else 3,
                        "label": "Disable Notification" if enabled else "Enable Notification",
                        "custom_id": f"notify:items:{notification.get_id()}:{'disable' if enabled else 'enable'}",
                    },
                    {
                        "type": 2,
                        "style": 4,
                        "label": "Delete Notification",
                        "custom_id": f"notify:items:{notification.get_id()}:delete",
                    },
                ],
            },
            {
                "type": 1,
                "components": [
                    {
                        "type": 2,
                        "style": 2,
                        "label": "Previous Notification",
                        "custom_id": f"notify:items:{-1 if previous_notif is None else previous_notif.get_id()}:goto",
                        "disabled": True if previous_notif is None else False,
                    },
                    {
                        "type": 2,
                        "style": 2,
                        "label": "Next Notification",
                        "custom_id": f"notify:items:{-2 if next_notif is None else next_notif.get_id()}:goto",
                        "disabled": True if next_notif is None else False,
                    },
                ],
            },
        ],
    }

    return payload


def item_notif_info(interaction, user: User, item: Item, *args, **kwargs):
    if "guild_id" in interaction:
        notifications = Notification.select().where(
            (Notification.n_type == 3)
            & (Notification.target == item.tid)
            & (
                (Notification.recipient_guild == int(interaction["guild_id"]))
                | ((Notification.recipient_guild == 0) & (Notification.invoker == user.tid))
            )
        )
    else:
        notifications = Notification.select().where(
            (Notification.n_type == 3)
            & (Notification.target == item.tid)
            & (Notification.recipient_guild == 0)
            & (Notification.invoker == user.tid)
        )

    notification_count = notifications.count()

    if notification_count == 0:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "No Notifications Found",
                        "description": "No item notifications were located in the database.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flag": 64,
            },
        }

    try:
        next_notif = notifications[1]
    except IndexError:
        next_notif = None

    return {
        "type": 4,
        "data": _generate_item_info_payload(
            notification=notifications.first(),
            item=item,
            current_number=1,
            total_count=notification_count,
            previous_notif=None,
            next_notif=next_notif,
        ),
    }


def items_switchboard(interaction, *args, **kwargs):
    user: User = kwargs["invoker"]

    try:
        subcommand = interaction["data"]["options"][0]["options"][0]["name"]
        subcommand_data = interaction["data"]["options"][0]["options"][0]["options"]
    except Exception:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Invalid Interaction Format",
                        "description": "Discord has returned an invalidly formatted interaction.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }

    item_name = find_list(subcommand_data, "name", "item")
    item: typing.Optional[Item] = None

    if item_name != -1:
        try:
            item = Item.get_by_id(int(item_name[1]["value"]))
        except (DoesNotExist, TypeError):
            return {
                "type": 4,
                "data": {
                    "embeds": [
                        {
                            "title": "Invalid Item Name",
                            "description": "A valid item ID is required for this command. If you have copied this "
                            "command, please retype the item name for the item ID to be properly registered.",
                            "color": SKYNET_ERROR,
                        },
                    ],
                    "flags": 64,
                },
            }

    if item is None and subcommand in ["info", "initialize"]:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Invalid Item Name",
                        "description": "A valid item name is required for this command.",
                        "color": SKYNET_ERROR,
                    },
                ],
                "flags": 64,
            },
        }

    if subcommand == "initialize":
        return item_notif_init(interaction, user, item, subcommand_data, *args, **kwargs)
    elif subcommand == "info":
        return item_notif_info(interaction, user, item, *args, **kwargs)
    elif subcommand == "list":
        return list_item_notifs(interaction, user, *args, **kwargs)
    else:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Command Not Found",
                        "description": "This command does not exist.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,
            },
        }


def items_autocomplete(interaction, *args, **kwargs):
    try:
        subcommand = interaction["data"]["options"][0]["options"][0]["name"]
        subcommand_data = interaction["data"]["options"][0]["options"][0]["options"]
    except Exception:
        return {
            "type": 8,
            "data": {
                "choices": [],
            },
        }

    if subcommand in ("initialize", "info"):
        for option in subcommand_data:
            if option.get("focused"):
                return {
                    "type": 8,
                    "data": {
                        "choices": [
                            {"name": item.name, "value": str(item.tid)}
                            for item in Item.select(Item.name, Item.tid)
                            .where(Item.name.startswith(option["value"]))
                            .limit(25)
                        ]
                    },
                }

    return {
        "type": 8,
        "data": {
            "choices": [],
        },
    }


def items_button_switchboard(interaction, *args, **kwargs):
    user = kwargs["invoker"]
    button_data = interaction["data"]["custom_id"].split(":")
    notification_id: str = button_data[2]
    effect = button_data[3]

    try:
        notification: Notification = Notification.get_by_id(notification_id)
    except DoesNotExist:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Notification Not Found",
                        "description": "The specified notification was not found in the database. Make sure it "
                        "hasn't already been deleted.",
                        "color": SKYNET_ERROR,
                    },
                ],
                "flags": 64,
            },
        }

    if effect == "goto":
        if notification.recipient_guild == 0:
            notifications = Notification.select().where(
                (Notification.n_type == 3) & (Notification.recipient_guild == 0) & (Notification.invoker == user.tid)
            )
        else:
            notifications = Notification.select().where(
                (Notification.n_type == 3)
                & (
                    (Notification.recipient_guild == int(interaction["guild_id"]))
                    | ((Notification.recipient_guild == 0) & (Notification.invoker == user.tid))
                )
            )

        notification_count = notifications.count()

        previous_notif = None
        current_notif = None
        next_notif = None
        current_count = 1

        while current_count <= notification_count:
            notif: Notification = notifications[current_count - 1]

            if notif.get_id() == notification.get_id():
                if current_count > 1:
                    previous_notif = notifications[current_count - 2]
                else:
                    previous_notif = None

                current_notif = notif

                try:
                    next_notif = notifications[current_count]
                except IndexError:
                    next_notif = None

                break

            current_count += 1

        item: typing.Optional[Item]
        try:
            item = Item.get_by_id(notification.target)
        except DoesNotExist:
            item = None

        return {
            "type": 7,
            "data": _generate_item_info_payload(
                notification=current_notif,
                item=item,
                current_number=current_count,
                total_count=notification_count,
                previous_notif=previous_notif,
                next_notif=next_notif,
            ),
        }

    elif effect == "delete":
        notification.delete_instance()

        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Notification Deleted",
                        "description": "The specified notification was deleted from the database.",
                        "color": SKYNET_GOOD,
                        "footer": {
                            "text": f"DB ID: {notification.get_id()}",
                        },
                    },
                ],
                "flags": 64,
            },
        }
    elif effect in ("disable", "enable"):
        if effect == "disable":
            if notification.enabled:
                Notification.update(enabled=False).where(Notification.id == notification.get_id()).execute()

                return {
                    "type": 4,
                    "data": {
                        "embeds": [
                            {
                                "title": "Notification Disabled",
                                "description": "The item notification has been enabled.",
                                "color": SKYNET_GOOD,
                                "footer": {
                                    "text": f"DB ID: {notification.get_id()}",
                                },
                            },
                        ],
                        "flags": 64,
                    },
                }
            else:
                return {
                    "type": 4,
                    "data": {
                        "embeds": [
                            {
                                "title": "Corrupted Button Data",
                                "description": "The notification is already disabled.",
                                "color": SKYNET_ERROR,
                                "footer": {
                                    "text": f"DB ID: {notification.get_id()}",
                                },
                            },
                        ],
                        "flags": 64,
                    },
                }
        elif effect == "enable":
            if not notification.enabled:
                Notification.update(enabled=True).where(Notification.id == notification.get_id()).execute()

                return {
                    "type": 4,
                    "data": {
                        "embeds": [
                            {
                                "title": "Notification Enabled",
                                "description": "The item notification has been enabled.",
                                "color": SKYNET_GOOD,
                                "footer": {
                                    "text": f"DB ID: {notification.get_id()}",
                                },
                            },
                        ],
                        "flags": 64,
                    },
                }
            else:
                return {
                    "type": 4,
                    "data": {
                        "embeds": [
                            {
                                "title": "Corrupted Button Data",
                                "description": "The notification is already enabled.",
                                "color": SKYNET_ERROR,
                                "footer": {
                                    "text": f"DB ID: {notification.get_id()}",
                                },
                            },
                        ],
                        "flags": 64,
                    },
                }
    else:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Corrupted Button Data",
                        "description": "The utilized button's data was corrupted.",
                        "color": SKYNET_ERROR,
                        "footer": {
                            "text": f"Invalid Data: {effect}",
                        },
                    },
                ],
                "flags": 64,
            },
        }
