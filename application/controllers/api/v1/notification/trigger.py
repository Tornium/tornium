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
import random
import re
import subprocess
import tempfile
import typing
import uuid

from flask import request
from peewee import DoesNotExist
from tornium_celery.tasks.api import discordpost
from tornium_commons.models import Notification, NotificationTrigger, Server
from tornium_commons.skyutils import SKYNET_GOOD

from controllers.api.v1.decorators import ratelimit, session_required
from controllers.api.v1.utils import api_ratelimit_response, make_exception_response

# regex modified based on https://stackoverflow.com/a/57639657/12941872
# Crontab in Elixir should only accept up to minutes
# TODO: Validate this regex
CRON_REGEX = (
    r"(@(annually|yearly|monthly|weekly|daily|hourly))|(@every (\d+(m|h))+)|((((\d+,)+\d+|(\d+(\/|-)\d+)|\d+|\*) ?){5})"
)

SELECTION_MAP = {
    # key: (public selection, user selection)
    "user": {
        "ammo": (PermissionError, "ammo"),
        "attacks": (PermissionError, "attacks"),
        "chain": (PermissionError, "bars"),
        "energy": (PermissionError, "bars"),
        "happy": (PermissionError, "bars"),
        "nerve": (PermissionError, "bars"),
        "gender": ("basic", "basic"),
        "level": ("basic", "basic"),
        "name": ("basic", "basic"),
        "player_id": ("basic", "basic"),
        "status": ("basic", "basic"),
        "defense": (PermissionError, "battlestats"),
        "defense_info": (PermissionError, "battlestats"),
        "defense_modifier": (PermissionError, "battlestats"),
        "dexterity": (PermissionError, "battlestats"),
        "dexterity_info": (PermissionError, "battlestats"),
        "dexterity_modifier": (PermissionError, "battlestats"),
        "speed": (PermissionError, "battlestats"),
        "speed_info": (PermissionError, "battlestats"),
        "speed_modifier": (PermissionError, "battlestats"),
        "strength": (PermissionError, "battlestats"),
        "strength_info": (PermissionError, "battlestats"),
        "strength_modifier": (PermissionError, "battlestats"),
        "total": (PermissionError, "battlestats"),
        "bazaar": ("bazaar", "bazaar"),
        "cooldowns": (PermissionError, "cooldowns"),
        "criminalrecord": ("criminalrecord", "criminalrecord"),
        "discord": ("discord", "discord"),
        "display": ("display", "display"),
        "education_completed": (PermissionError, "education"),
        "education_current": (PermissionError, "education"),
        "education_timeleft": (PermissionError, "education"),
        "equipment": (PermissionError, "equipment"),
        "events": (PermissionError, "events"),
        "activegym": (PermissionError, "gym"),
        "halloffame": (PermissionError, "hof"),
        "honors_awarded": (PermissionError, "honors"),
        "honors_time": (PermissionError, "honors"),
        "icons": ("icons", "icons"),
        "jobpoints": (PermissionError, "jobpoints"),
        "log": (PermissionError, PermissionError),
        "selections": ("lookup", "lookup"),
        "medals_awarded": ("medals", "medals"),
        "medals_time": ("medals", "medals"),
        "merits": (PermissionError, "merits"),
        "messages": (PermissionError, "messages"),
        "missions": (PermissionError, "missions"),
        "cayman_bank": (PermissionError, "money"),
        "city_bank": (PermissionError, "money"),
        "company_funds": (PermissionError, "money"),
        "daily_networth": (PermissionError, "money"),
        "money_onhand": (PermissionError, "money"),
        "points": (PermissionError, "money"),
        "vault_amount": (PermissionError, "money"),
        "networth": (PermissionError, "networth"),
        "notifications": (PermissionError, "notifications"),
        "book_perks": (PermissionError, "perks"),
        "education_perks": (PermissionError, "perks"),
        "enhancer_perks": (PermissionError, "perks"),
        "faction_perks": (PermissionError, "perks"),
        "job_perks": (PermissionError, "perks"),
        "merit_perks": (PermissionError, "perks"),
        "property_perks": (PermissionError, "perks"),
        "stock_perks": (PermissionError, "perks"),
        "personalstats": ("personalstats", "personalstats"),
        "age": ("profile", "profile"),
        "awards": ("profile", "profile"),
        "basicicons": ("profile", "profile"),
        "competition": ("profile", "profile"),
        "donator": ("profile", "profile"),
        "enemies": ("profile", "profile"),
        "faction": ("profile", "profile"),
        "forum_posts": ("profile", "profile"),
        "friends": ("profile", "profile"),
        "honor": ("profile", "profile"),
        "job": ("profile", "profile"),
        "karma": ("profile", "profile"),
        "last_action": ("profile", "profile"),
        "life": ("profile", "profile"),
        "married": ("profile", "profile"),
        "profile_image": ("profile", "profile"),
        "property": ("profile", "profile"),
        "property_id": ("profile", "profile"),
        "rank": ("profile", "profile"),
        "signup": ("profile", "profile"),
        "states": ("profile", "profile"),
        "properties": ("properties", "properties"),
        "baned": ("publicstatus", "publicstatus"),
        "playername": ("publicstatus", "publicstatus"),
        "userID": ("publicstatus", "publicstatus"),
        "refills": (PermissionError, "refills"),
        "reports": (PermissionError, "reports"),
        "revives": (PermissionError, "revives"),
        "bootlegging": (PermissionError, "skills"),
        "burglary": (PermissionError, "skills"),
        "card_skimming": (PermissionError, "skills"),
        "cracking": (PermissionError, "skills"),
        "disposal": (PermissionError, "skills"),
        "forgery": (PermissionError, "skills"),
        "graffiti": (PermissionError, "skills"),
        "hunting": (PermissionError, "skills"),
        "hustling": (PermissionError, "skills"),
        "pickpocketing": (PermissionError, "skills"),
        "racing": (PermissionError, "skills"),
        "reviving": (PermissionError, "skills"),
        "search_for_cash": (PermissionError, "skills"),
        "shoplifting": (PermissionError, "skills"),
        "stocks": (PermissionError, "stocks"),
        "timestamp": (PermissionError, "timestamp"),
        "travel": (PermissionError, "travel"),
        "weaponxp": (PermissionError, "weaponxp"),
        "workstats": (PermissionError, "workstats"),
    },
    "faction": {  # TODO: Require faction AA for all self faction fields
        "applications": (PermissionError, "applications"),
        "armor": (PermissionError, "armor"),
        "armorynews": (PermissionError, "armorynews"),
        "attacknews": (PermissionError, "attacknews"),
        "attacks": (PermissionError, "attacks"),
        "age": ("basic", "basic"),
        "best_chain": ("basic", "basic"),
        "capacity": ("basic", "basic"),
        "co-leader": ("basic", "basic"),
        "ID": ("basic", "basic"),
        "leader": ("basic", "basic"),
        "members": ("basic", "basic"),
        "name": ("basic", "basic"),
        "peace": ("basic", "basic"),
        "raid_wars": ("basic", "basic"),
        "rank": ("basic", "basic"),
        "ranked_wars": ("basic", "basic"),
        "respect": ("basic", "basic"),
        "tag": ("basic", "basic"),
        "tag_image": ("basic", "basic"),
        "territory_wars": ("basic", "basic"),
        "boosters": (PermissionError, "boosters"),
        "caches": (PermissionError, "caches"),
        "cesium": (PermissionError, "cesium"),
        "chain": ("chain", "chain"),
        "chain_report": (PermissionError, "chain_report"),
        "chains": (PermissionError, "chains"),
        "contributors": (
            PermissionError,
            PermissionError,
        ),  # TODO: Not yet support... need to determine which stat is required
        "crimeexp": (PermissionError, "crimeexp"),
        "crimenews": (PermissionError, "crimenews"),
        "crimes": (PermissionError, "crimes"),
        "money": (PermissionError, "currency"),
        "points": (PermissionError, "currency"),
        "donations": (PermissionError, "donations"),
        "drugs": (PermissionError, "drugs"),
        "fundsnews": (PermissionError, "fundsnews"),
        "mainnews": (PermissionError, "mainnews"),
        "medical": (PermissionError, "medical"),
        "membershipnews": (PermissionError, "membershipnews"),
        "positions": (PermissionError, "positions"),
        "rankedwars": ("rankedwars", "rankedwars"),
        "reports": (PermissionError, "reports"),
        "revives": (PermissionError, "revives"),
        "stats": (PermissionError, "stats"),
        "temporary": (PermissionError, "temporary"),
        "territory": ("territory", "territory"),
        "territorynews": (PermissionError, "territorynews"),
        "upgrades": (PermissionError, "upgrades"),
        "weapons": (PermissionError, "weapons"),
    },
    "company": {},
    "torn": {},
    "factionv2": {},
}


def extract_selections(code: str, resource: str, resource_self: bool = False) -> typing.Set[str]:
    selections = set()
    attributes = set()

    resource = re.escape(resource)
    for match in re.finditer(rf"{resource}\[\s*[\"']([^\"']+)[\"']\s*\]|{resource}\.([a-zA-Z_]\w*)", code):
        attributes.add(match.groups()[1])

    for attribute in attributes:
        try:
            selection = SELECTION_MAP[resource][attribute][int(resource_self)]
        except KeyError:
            raise ValueError(attribute)

        if selection is PermissionError:
            raise PermissionError(attribute)

        selections.add(selection)

    return selections


@session_required
@ratelimit
def create_trigger(trigger_id=None, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    if trigger_id is not None and request.method == "PUT":
        update = True
    elif trigger_id is None and request.method == "POST":
        update = False
    else:
        return make_exception_response("0000", key)

    trigger_name: str = data.get("name", f"trigger-{kwargs['user'].tid}-{random.randint(0, 100)}")
    trigger_description: str = data.get("description", "")
    trigger_resource: typing.Optional[str] = data.get("resource")
    trigger_cron: str = data.get("cron", "* * * * *")
    trigger_code: typing.Optional[str] = data.get("code", None)
    trigger_parameters: typing.Dict[str, str] = data.get("parameters", {})
    trigger_message_type = data.get("message_type", 0)
    trigger_message_template = data.get("message_template", "")

    if not isinstance(trigger_name, str):
        return make_exception_response("1000", key, details={"message": "Invalid trigger name"})
    elif len(trigger_name) == 0:
        return make_exception_response("1000", key, details={"message" "Invalid trigger name (length)"})

    # TODO: Validate the user does not have a trigger named the same thing
    # TODO: Create unique index on (user, trigger_name)

    if not isinstance(trigger_description, str):
        return make_exception_response(
            "1000",
            key,
            details={
                "message": "Invalid trigger description",
            },
        )

    if trigger_resource is None:
        return make_exception_response(
            "1000",
            key,
            details={
                "message": "invalid trigger resource",
            },
        )
    elif trigger_resource not in ("user", "faction", "company", "factionv2"):
        return make_exception_response(
            "1000",
            key,
            details={
                "message": "invalid trigger resource",
            },
        )

    if not isinstance(trigger_cron, str):
        return make_exception_response(
            "1000",
            key,
            details={
                "message": "Invalid trigger cron",
            },
        )
    elif not re.match(CRON_REGEX, trigger_cron):
        return make_exception_response(
            "1000",
            key,
            details={
                "message": "Invalid trigger cron (regex)",
            },
        )

    if trigger_code is None or not isinstance(trigger_code, str) or len(trigger_code) == 0:
        return make_exception_response(
            "1000",
            key,
            details={
                "message": "Missing Lua code",
            },
        )

    if not isinstance(trigger_parameters, dict):
        return make_exception_response(
            "1000",
            key,
            details={
                "message": "Invalid trigger parameters type",
            },
        )

    if not isinstance(trigger_message_type, int):
        return make_exception_response(
            "1000",
            key,
            details={
                "message": "Invlaid trigger message type",
            },
        )
    # TODO: Improve the contract for `trigger_message_type` in the API
    if trigger_message_type == 0:
        trigger_message_type = "update"
    elif trigger_message_type == 1:
        trigger_message_type = "send"
    else:
        return make_exception_response(
            "1000",
            key,
            details={
                "message": "Invlaid trigger message type",
            },
        )

    if not isinstance(trigger_message_template, str) or len(trigger_message_template) == 0:
        return make_exception_response(
            "1000",
            key,
            details={
                "message": "Missing trigger message template",
            },
        )

    # We want to make sure that the provided Lua code is syntactically valid before providing it to Elixir worker
    # to avoid excess load on the worker and the IP ratelimit
    with tempfile.NamedTemporaryFile() as fp:
        fp.write(trigger_code.encode("utf-8"))
        fp.seek(0)

        print(fp.read())
        print(fp.name)

        ret = subprocess.run(["luac", "-p", fp.name], capture_output=True, timeout=1)

        if ret.returncode == 1:
            return make_exception_response("0000", key, details={"error": ret.stderr.decode("utf-8")})

    try:
        # Allow private selections for creating the trigger as resource ID is not known
        selections = extract_selections(trigger_code, trigger_resource, resource_self=True)
    except PermissionError as e:
        attribute = e.args[0]

        return make_exception_response("0000", key, details={"error": f"Private data attribute: {attribute}"})
    except ValueError as e:
        attribute = e.args[0]

        return make_exception_response("0000", key, details={"error": f"Invalid data attribute: {attribute}"})

    if update:
        NotificationTrigger.update(
            name=trigger_name,
            description=trigger_description,
            cron=trigger_cron,
            resource=trigger_resource,
            selections=selections,
            code=trigger_code,
            parameters=trigger_parameters,
            message_type=trigger_message_type,
            message_template=trigger_message_template,
        ).where(NotificationTrigger.tid == uuid.UUID(trigger_id)).execute()
    else:
        NotificationTrigger.create(
            tid=uuid.uuid4(),
            name=trigger_name,
            description=trigger_description,
            owner=kwargs["user"],
            cron=trigger_cron,
            resource=trigger_resource,
            selections=selections,
            code=trigger_code,
            parameters=trigger_parameters,
            message_type=trigger_message_type,
            message_template=trigger_message_template,
            public=False,
            official=False,
        )

    # TODO: Return trigger data

    return {}, 200, api_ratelimit_response(key)


@session_required
@ratelimit
def list_triggers(*args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    limit = request.args.get("limit", 10)
    offset = request.args.get("offset", 0)
    official = request.args.get("official", "0") == "1"

    if (not isinstance(limit, str) or not limit.isdigit()) and not isinstance(limit, int):
        return make_exception_response("1000", key, details={"error": "Invalid limit value"})
    elif int(limit) <= 0:
        return make_exception_response("1000", key, details={"error": "Invalid limit value"})
    elif (not isinstance(offset, str or not limit.isdigit())) and not isinstance(offset, int):
        return make_exception_response("1000", key, details={"error": "Invalid offset value"})
    elif int(offset) < 0:
        return make_exception_response("1000", key, details={"error": "Invalid offset value"})

    limit = int(limit)
    offset = int(offset)
    official = bool(official)

    user_triggers = NotificationTrigger.select().where(
        (NotificationTrigger.owner == kwargs["user"]) & (NotificationTrigger.official == official)
    )
    filtered_user_triggers = user_triggers.offset(offset).limit(limit)

    return (
        {
            "count": user_triggers.count(),
            "triggers": [trigger.as_dict() for trigger in filtered_user_triggers],
        },
        200,
        api_ratelimit_response(key),
    )


@session_required
@ratelimit
def setup_trigger_guild(trigger_id, guild_id: int, *args, **kwargs):
    data = json.loads(request.get_data().decode("utf-8"))
    key = f"tornium:ratelimit:{kwargs['user'].tid}"

    try:
        trigger_uuid = uuid.UUID(trigger_id)
    except ValueError:
        return make_exception_response("1000", key, details={"message": "Invalid trigger UUID"})

    try:
        trigger: NotificationTrigger = (
            NotificationTrigger.select().where(NotificationTrigger.tid == trigger_uuid).get()
        )  # TODO: Limit selections
    except DoesNotExist:
        return make_exception_response("1400", key)

    if trigger.owner.tid != kwargs["user"].tid and not trigger.official:
        return make_exception_response("4022", key)

    try:
        guild: Server = Server.select().where(Server.sid == guild_id).get()
        # TODO: Limit selections
    except DoesNotExist:
        return make_exception_response("1001", key)

    try:
        channel_id = int(data["channel_id"])
    except (KeyError, ValueError, TypeError):
        return make_exception_response("1001", key)

    try:
        resource_id = int(data["resource_id"])
    except (KeyError, ValueError, TypeError):
        return make_exception_response("1000", key, details={"message": "Invalid resource ID"})

    try:
        one_shot = data["one_shot"]
    except (KeyError, ValueError, TypeError):
        return make_exception_response("1000", key, details={"message": "Invalid one-shot value"})

    if not isinstance(one_shot, bool):
        return make_exception_response("1000", key, details={"message": "Invalid one-shot value"})

    try:
        parameters = data["parameters"]
    except (KeyError, ValueError, TypeError):
        return make_exception_response("1402", key)

    if not isinstance(parameters, dict):
        return make_exception_response("1402", key)
    elif not all(isinstance(key, str) for key in parameters.keys()):
        return make_exception_response("1402", key)
    elif parameters.keys() != trigger.parameters.keys():
        return make_exception_response("1402", key, details={"message": "Invalid parameter key"})

    nid = uuid.uuid4()
    notification: Notification = Notification.create(
        nid=nid,
        trigger=trigger_uuid,
        user=kwargs["user"].tid,
        enabled=True,
        server=guild.sid,
        channel_id=channel_id,
        resource_id=resource_id,
        one_shot=one_shot,
        parameters=parameters,
    )

    if guild.notifications_config is not None and guild.notifications_config.log_channel not in (0, None):
        discordpost.delay(
            f"channels/{guild.notifications_config.log_channel}",
            {
                "embeds": [
                    {
                        "title": "Notification Created",
                        "description": f"{kwargs['user'].user_str_self()} has created a notification against {trigger.name}.",
                        "footer": {
                            "text": f"ID: {nid}",
                        },
                        "color": SKYNET_GOOD,
                    }
                ]
            },
        )

    return (
        {
            "nid": notification.nid,
        },
        200,
        api_ratelimit_response(key),
    )