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

import pathlib
import re
import typing
import uuid

import toml
from tornium_commons.models import NotificationTrigger

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
    "faction": {
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


def has_restricted_selection(code: str, resource: str) -> bool:
    attributes = set()

    resource = re.escape(resource)
    for match in re.finditer(rf"{resource}\[\s*[\"']([^\"']+)[\"']\s*\]|{resource}\.([a-zA-Z_]\w*)", code):
        attributes.add(match.groups()[1])

    for attribute in attributes:
        try:
            selection = SELECTION_MAP[resource][attribute][0]
        except KeyError:
            raise ValueError(attribute)

        if selection is PermissionError:
            return True

    return False


class TriggerConfig(typing.TypedDict):
    uuid: str
    name: str
    description: str
    owner: int


class ImplementationConfig(typing.TypedDict):
    cron: str
    resource: typing.Literal["faction", "user"]
    selections: typing.List[str]
    message_type: typing.Literal["update", "send"]
    parameters: typing.Dict[str, str]


class Config(typing.TypedDict):
    trigger: TriggerConfig
    implementation: ImplementationConfig


def load_trigger(path: pathlib.Path, official: bool = False):
    """
    Load a notification trigger by path of its directory into the database

    Parameters
    ----------
    path : pathlib.Path
        Path to the directory containing the trigger's code and others

    official : bool
        Boolean flag for whether the trigger is an official trigger
    """

    with open(f"{path}/config.toml", "r") as f:
        config_data: Config = toml.load(f)

    with open(f"{path}/code.lua", "r") as f:
        code: str = f.read()

    with open(f"{path}/message.liquid", "r") as f:
        template: str = f.read()

    # TODO: Validate data provided by files

    NotificationTrigger.insert(
        tid=uuid.UUID(config_data["trigger"]["uuid"]),
        name=config_data["trigger"]["name"],
        description=config_data["trigger"]["description"],
        owner=config_data["trigger"]["owner"],
        cron=config_data["implementation"]["cron"],
        resource=config_data["implementation"]["resource"],
        selections=config_data["implementation"]["selections"],
        code=code,
        parameters=config_data["implementation"]["parameters"],
        message_type=config_data["implementation"]["message_type"],
        message_template=template,
        restricted_data=has_restricted_selection(code, config_data["implementation"]["resource"]),
        official=official,
    ).on_conflict(
        conflict_target=[NotificationTrigger.tid],
        preserve=[
            NotificationTrigger.name,
            NotificationTrigger.description,
            # NOTE: Skip updating the trigger's owner for security, this can be changed in the database
            NotificationTrigger.cron,
            NotificationTrigger.resource,
            NotificationTrigger.selections,
            NotificationTrigger.code,
            NotificationTrigger.parameters,
            NotificationTrigger.message_type,
            NotificationTrigger.message_template,
            NotificationTrigger.restricted_data,
            NotificationTrigger.official,
        ],
    ).execute()
