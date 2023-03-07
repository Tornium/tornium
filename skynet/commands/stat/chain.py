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

import json
import math
import random
import time
import typing

import mongoengine
import requests
from mongoengine.queryset.visitor import Q

from tornium_celery.tasks.api import discordpatch, discordpost
from tornium_celery.tasks.user import update_user
from tornium_commons.errors import TornError, NetworkingError
from tornium_commons.formatters import commas, find_list, rel_time
from tornium_commons.models import StatModel, UserModel
from tornium_commons.skyutils import SKYNET_ERROR, SKYNET_GOOD

from models.user import User
from skynet.skyutils import get_admin_keys, invoker_exists


@invoker_exists
def chain(interaction, *args, **kwargs):
    start = time.time()
    user: UserModel = kwargs["invoker"]

    if "options" in interaction["data"]:
        length = find_list(interaction["data"]["options"], "name", "length")
        ff = find_list(interaction["data"]["options"], "name", "fairfight")
        variance = 0.01
    else:
        length = 12
        ff = 3
        variance = 0.01

    if type(length) != int:
        length = length[1]["value"]
    else:
        length = 12

    if type(ff) != int:
        ff = round(ff[1]["value"], 2)
    else:
        ff = 3

    if ff == 3:
        variance = 0

    admin_keys = kwargs.get("admin_keys")

    if admin_keys is None:
        admin_keys = get_admin_keys(interaction)

    if len(admin_keys) == 0:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "No API Keys",
                        "description": "No API keys were found to be run for this command. Please sign into "
                        "Tornium or run this command in a server with signed-in admins.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }

    try:
        discordpost(
            f"interactions/{interaction['id']}/{interaction['token']}/callback",
            payload={"type": 5},
        )
    except requests.exceptions.JSONDecodeError:
        pass
    except json.JSONDecodeError:
        pass

    if user.battlescore == 0:
        return {
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "Stats Missing",
                        "description": "The user's battle stats could not be located in the database. Please sign into "
                        "Tornium.",
                        "color": SKYNET_ERROR,
                    }
                ],
                "flags": 64,  # Ephemeral
            },
        }

    # f = fair fight
    # v = variance
    # d = defender's stat score
    # a = attacker's stat score
    #
    # f +- v = 1 + 8/3 * d/a
    # 0.375 * a * (f +- v - 1) = d
    #
    # f = 11/3 is equal ratio of d/a
    # f = 17/5 is 9/10 ratio of d/a

    if ff == 3:
        stat_entries: mongoengine.QuerySet = StatModel.objects(
            (Q(globalstat=True) | Q(addedid=user.tid) | Q(addedfactiontid=user.factionid))
            & Q(battlescore__gte=(0.375 * user.battlescore * (ff - 1)))
            & Q(battlescore__lte=(0.375 * user.battlescore * 2.4))
        )
    else:
        stat_entries: mongoengine.QuerySet = StatModel.objects(
            (Q(globalstat=True) | Q(addedid=user.tid) | Q(addedfactiontid=user.factionid))
            & Q(battlescore__gte=(0.375 * user.battlescore * (ff - variance - 1)))
            & Q(battlescore__lte=(0.375 * user.battlescore * (ff + variance - 1)))
        )

    if stat_entries.count() == 0:
        discordpatch(
            f"webhooks/{interaction['application_id']}/{interaction['token']}/messages/@original",
            payload={
                "embeds": [
                    {
                        "title": "No Targets Located",
                        "description": "No chain targets could be located with the following settings.",
                        "color": SKYNET_ERROR,
                        "fields": [
                            {
                                "name": "Length",
                                "value": length,
                                "inline": True,
                            },
                            {
                                "name": "Fair Fight",
                                "value": str(ff),
                                "inline": True,
                            },
                            {
                                "Name": "Variance",
                                "value": str(variance),
                                "inline": True,
                            },
                        ],
                    }
                ]
            },
        )

    stat_entries: list = list(set(stat_entries.all().values_list("tid")))
    random.shuffle(stat_entries)
    jsonified_stat_entries = []

    targets = {}
    targets_updated = 0

    for stat_entry in stat_entries:
        stat: StatModel = (
            StatModel.objects(
                Q(tid=stat_entry) & (Q(globalstat=True) | Q(addedid=user.tid) | Q(addedfactiontid=user.factionid))
            )
            .order_by("-timeadded")
            .first()
        )

        if stat.battlescore > user.battlescore:
            continue

        if stat_entry in targets:
            target = targets[stat_entry]
        else:
            target: typing.Optional[UserModel] = None

            if targets_updated <= 50:
                try:
                    update_user(random.choice(admin_keys), tid=stat.tid, wait=True)
                    target = UserModel.objects(tid=stat.tid).first()
                    targets_updated += 1
                except TornError:
                    if int(time.time()) - target.last_refresh <= 2592000:  # One day
                        pass
                    else:
                        continue
                except NetworkingError as e:
                    if e.code == 408:
                        if int(time.time()) - target.last_refresh <= 2592000:  # One day
                            pass
                        else:
                            continue
                    else:
                        raise e

        target_ff = 1 + 8 / 3 * (stat.battlescore / user.battlescore)

        if target_ff > 3:
            target_ff = 3
        if target.level == 0:
            continue

        try:
            base_respect = round((math.log(target.level) + 1) / 4, 2)
        except ValueError:
            continue

        jsonified_stat_entries.append(
            {
                "statid": str(stat.id),
                "tid": stat.tid,
                "battlescore": stat.battlescore,
                "timeadded": stat.timeadded,
                "ff": target_ff,
                "respect": round(base_respect * target_ff, 2),
                "user": {
                    "tid": target.tid,
                    "name": target.name,
                    "username": f"{target.name} [{target.tid}]",
                    "level": target.level,
                    "last_refresh": target.last_refresh,
                    "factionid": target.factionid,
                    "status": target.status,
                    "last_action": target.last_action,
                },
            }
        )

    embed = {
        "title": f"Chain List for {user.name} [{user.tid}]",
        "fields": [],
        "color": SKYNET_GOOD,
        "footer": {"text": ""},
    }

    jsonified_stat_entries = sorted(jsonified_stat_entries, key=lambda d: d["respect"], reverse=True)
    stat_count = 0

    for stat_entry in jsonified_stat_entries:
        if stat_count >= length:
            break

        embed["fields"].append(
            {
                "name": f"{stat_entry['user']['name']} [{stat_entry['user']['tid']}]",
                "value": f"Stat Score: {commas(stat_entry['battlescore'])}\nRespect: {stat_entry['respect']}\nLast Update: {rel_time(stat_entry['timeadded'])}",
                "inline": True,
            }
        )

        stat_count += 1

    embed["description"] = f"Showing {stat_count} of {len(jsonified_stat_entries)} chain targets..."
    embed["footer"] = {"text": f"Run time: {round(time.time() - start, 2)} seconds"}

    discordpatch(
        f"webhooks/{interaction['application_id']}/{interaction['token']}/messages/@original",
        payload={"embeds": [embed]},
    )
