# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import datetime
import random

from honeybadger import honeybadger
import requests
from mongoengine.queryset.visitor import Q

from models.factionmodel import FactionModel
from models.factionstakeoutmodel import FactionStakeoutModel
from models.servermodel import ServerModel
from models.usermodel import UserModel
from models.userstakeoutmodel import UserStakeoutModel
from tasks import celery_app, discordpost, logger, tornget
import utils


@celery_app.task
def user_stakeouts():
    stakeout: UserStakeoutModel
    for stakeout in UserStakeoutModel.objects():
        user_stakeout.delay(stakeout=stakeout.tid)


@celery_app.task
def faction_stakeouts():
    stakeout: FactionStakeoutModel
    for stakeout in FactionStakeoutModel.objects():
        faction_stakeout.delay(stakeout=stakeout.tid)


@celery_app.task
def user_stakeout(stakeout: int, requests_session=None, key=None):
    stakeout: UserStakeoutModel = UserStakeoutModel.objects(tid=stakeout).first()

    if stakeout is None:
        return

    try:
        if key is not None:
            data = tornget(
                f"user/{stakeout.tid}?selections=", key=key, session=requests_session
            )
        else:
            if len(stakeout.guilds) == 0:
                return

            guild: ServerModel = ServerModel.objects(
                sid=int(random.choice(list(stakeout.guilds)))
            ).first()

            if guild is None and len(list(stakeout.guilds)) == 1:
                return
            elif guild is None and len(list(stakeout.guilds)) > 1:
                guilds = random.sample(
                    list(stakeout.guilds), k=len(list(stakeout.guilds))
                )
                guild_discovered = False

                for guild_id in guilds:
                    guild: ServerModel = ServerModel.objects(sid=int(guild_id)).first()

                    if guild is not None and len(guild.admins) != 0:
                        guild_discovered = True
                        break

                if not guild_discovered:
                    return

            if len(guild.admins) == 0:
                return

            admin: UserModel = UserModel.objects(
                tid=random.choice(guild.admins)
            ).first()
            data = tornget(
                f"user/{stakeout.tid}?selections=",
                key=admin.key,
                session=requests_session,
            )
    except utils.TornError as e:
        logger.exception(e)
        honeybadger.notify(e, context={"code": e.code, "endpoint": e.endpoint})
        return
    except utils.MissingKeyError:
        return
    except Exception as e:
        logger.exception(e)
        honeybadger.notify(e)
        return

    stakeout_data = stakeout.data
    stakeout.last_update = utils.now()
    stakeout.data = data
    stakeout.save()

    for guildid, guild_stakeout in stakeout.guilds.items():
        if len(guild_stakeout["keys"]) == 0:
            continue
        elif guild_stakeout["channel"] == 0:
            continue

        server: ServerModel = ServerModel.objects(sid=guildid).first()

        if server is None:
            continue
        elif server.config["stakeouts"] == 0:
            continue

        if (
            "level" in guild_stakeout["keys"]
            and data["level"] != stakeout_data["level"]
        ):
            payload = {
                "embeds": [
                    {
                        "title": "Level Change",
                        "description": f'The level of staked out user {data["name"]} has changed from '
                        f'{stakeout_data["level"]} to {data["level"]}.',
                        "timestamp": datetime.datetime.utcnow().isoformat(),
                        "footer": {"text": utils.torn_timestamp()},
                        "components": [
                            {
                                "type": 1,
                                "components": [
                                    {
                                        "type": 2,
                                        "style": 5,
                                        "label": "User",
                                        "url": f"https://www.torn.com/profiles.php?XID={data['player_id']}",
                                    }
                                ],
                            }
                        ],
                    }
                ]
            }
            try:
                discordpost.delay(
                    f'channels/{guild_stakeout["channel"]}/messages',
                    payload=payload,
                    dev=server.skynet,
                )
            except Exception as e:
                logger.exception(e)
                return

        if (
            "status" in guild_stakeout["keys"]
            and data["status"]["state"] != stakeout_data["status"]["state"]
        ):
            payload = {
                "embeds": [
                    {
                        "title": "Status Change",
                        "description": f'The status of staked out user {data["name"]} has changed from '
                        f'{stakeout_data["status"]["state"]} to {data["status"]["state"]}.',
                        "timestamp": datetime.datetime.utcnow().isoformat(),
                        "footer": {"text": utils.torn_timestamp()},
                        "components": [
                            {
                                "type": 1,
                                "components": [
                                    {
                                        "type": 2,
                                        "style": 5,
                                        "label": "User",
                                        "url": f"https://www.torn.com/profiles.php?XID={data['player_id']}",
                                    }
                                ],
                            }
                        ],
                    }
                ]
            }
            try:
                discordpost.delay(
                    f'channels/{guild_stakeout["channel"]}/messages',
                    payload=payload,
                    dev=server.skynet,
                )
            except Exception as e:
                logger.exception(e)
                return

        if (
            "flyingstatus" in guild_stakeout["keys"]
            and (
                data["status"]["state"] in ["Travelling", "In"]
                or stakeout_data["status"]["state"] in ["Travelling", "In"]
            )
            and data["status"]["state"] != stakeout_data["status"]["state"]
        ):
            payload = {
                "embeds": [
                    {
                        "title": "Flying Status Change",
                        "description": f'The flying status of staked out user {data["name"]} has changed from '
                        f'{stakeout_data["status"]["state"]} to {data["status"]["state"]}.',
                        "timestamp": datetime.datetime.utcnow().isoformat(),
                        "footer": {"text": utils.torn_timestamp()},
                        "components": [
                            {
                                "type": 1,
                                "components": [
                                    {
                                        "type": 2,
                                        "style": 5,
                                        "label": "User",
                                        "url": f"https://www.torn.com/profiles.php?XID={data['player_id']}",
                                    }
                                ],
                            }
                        ],
                    }
                ]
            }
            try:
                discordpost.delay(
                    f'channels/{guild_stakeout["channel"]}/messages',
                    payload=payload,
                    dev=server.skynet,
                )
            except Exception as e:
                logger.exception(e)
                return

        if (
            "online" in guild_stakeout["keys"]
            and data["last_action"]["status"] == "Online"
            and stakeout_data["last_action"]["status"] in ["Offline", "Idle"]
        ):
            payload = {
                "embeds": [
                    {
                        "title": "Activity Change",
                        "description": f'The activity of staked out user {data["name"]} has changed from '
                        f'{stakeout_data["last_action"]["status"]} to {data["last_action"]["status"]}.',
                        "timestamp": datetime.datetime.utcnow().isoformat(),
                        "footer": {"text": utils.torn_timestamp()},
                        "components": [
                            {
                                "type": 1,
                                "components": [
                                    {
                                        "type": 2,
                                        "style": 5,
                                        "label": "User",
                                        "url": f"https://www.torn.com/profiles.php?XID={data['player_id']}",
                                    }
                                ],
                            }
                        ],
                    }
                ]
            }
            try:
                discordpost.delay(
                    f'channels/{guild_stakeout["channel"]}/messages',
                    payload=payload,
                    dev=server.skynet,
                )
            except Exception as e:
                logger.exception(e)
                return

        if (
            "offline" in guild_stakeout["keys"]
            and data["last_action"]["status"] in ["Offline", "Idle"]
            and stakeout_data["last_action"]["status"] in ["Online", "Idle"]
            and data["last_action"]["status"] != stakeout_data["last_action"]["status"]
        ):
            if (
                data["last_action"]["status"] == "Idle"
                and datetime.datetime.utcnow().timestamp()
                - data["last_action"]["timestamp"]
                < 300
            ):
                continue
            elif (
                data["last_action"]["status"] == "Idle"
                and stakeout_data["last_action"]["status"] == "Idle"
            ):
                continue

            payload = {
                "embeds": [
                    {
                        "title": "Activity Change",
                        "description": f'The activity of staked out user {data["name"]} has changed from '
                        f'{stakeout_data["last_action"]["status"]} to {data["last_action"]["status"]}.',
                        "timestamp": datetime.datetime.utcnow().isoformat(),
                        "footer": {"text": utils.torn_timestamp()},
                        "components": [
                            {
                                "type": 1,
                                "components": [
                                    {
                                        "type": 2,
                                        "style": 5,
                                        "label": "User",
                                        "url": f"https://www.torn.com/profiles.php?XID={data['player_id']}",
                                    }
                                ],
                            }
                        ],
                    }
                ]
            }
            try:
                discordpost.delay(
                    f'channels/{guild_stakeout["channel"]}/messages',
                    payload=payload,
                    dev=server.skynet,
                )
            except Exception as e:
                logger.exception(e)
                return


@celery_app.task
def faction_stakeout(stakeout: int, requests_session=None, key=None):
    stakeout: FactionStakeoutModel = FactionStakeoutModel.objects(tid=stakeout).first()

    if stakeout is None:
        return

    try:
        if key is not None:
            data = tornget(
                f"faction/{stakeout.tid}?selections=basic,territory",
                key=key,
                session=requests_session,
            )
        else:
            if len(stakeout.guilds) == 0:
                return

            guild: ServerModel = ServerModel.objects(
                sid=int(random.choice(list(stakeout.guilds)))
            ).first()
            if guild is None and len(list(stakeout.guilds)) == 1:
                return
            elif guild is None and len(list(stakeout.guilds)) > 1:
                guilds = random.sample(
                    list(stakeout.guilds), k=len(list(stakeout.guilds))
                )
                guild_discorvered = False
                for guild_id in guilds:
                    guild: ServerModel = ServerModel.objects(sid=int(guild_id)).first()
                    if guild is not None and len(guild.admins) != 0:
                        guild_discorvered = True
                        break
                if not guild_discorvered:
                    return

            if len(guild.admins) == 0:
                return

            admin: UserModel = UserModel.objects(
                tid=random.choice(guild.admins)
            ).first()
            data = tornget(
                f"faction/{stakeout.tid}?selections=basic,territory",
                key=admin.key,
                session=requests_session,
            )
    except utils.TornError as e:
        logger.exception(e)
        honeybadger.notify(e, context={"code": e.code, "endpoint": e.endpoint})
        return
    except utils.MissingKeyError:
        return
    except Exception as e:
        logger.exception(e)
        honeybadger.notify(e)
        return

    stakeout_data = stakeout.data
    stakeout.last_update = utils.now()
    stakeout.data = data
    stakeout.save()

    for guildid, guild_stakeout in stakeout.guilds.items():
        if len(guild_stakeout["keys"]) == 0:
            continue
        elif guild_stakeout["channel"] == 0:
            continue

        server: ServerModel = ServerModel.objects(sid=guildid).first()

        if server.config["stakeouts"] == 0:
            continue

        # stakeout_data: data from the previous minute
        # data: data from this minute

        if (
            "territory" in guild_stakeout["keys"]
            and data["territory"] != stakeout_data["territory"]
        ):
            for territoryid, territory in stakeout_data["territory"].items():
                if territoryid not in data["territory"]:
                    payload = {
                        "embeds": [
                            {
                                "title": "Territory Removed",
                                "description": f'The territory {territoryid} of faction {data["name"]} has '
                                f"been dropped.",
                                "timestamp": datetime.datetime.utcnow().isoformat(),
                                "footer": {"text": utils.torn_timestamp()},
                                "components": [
                                    {
                                        "type": 1,
                                        "components": [
                                            {
                                                "type": 2,
                                                "style": 5,
                                                "label": "Territory",
                                                "url": f"",
                                                "disabled": True,
                                            },
                                            {
                                                "type": 2,
                                                "style": 5,
                                                "label": "Faction",
                                                "url": f"https://www.torn.com/factions.php?step=profile&ID={data['ID']}",
                                            },
                                        ],
                                    }
                                ],
                            }
                        ]
                    }
                    try:
                        discordpost.delay(
                            f'channels/{guild_stakeout["channel"]}/messages',
                            payload=payload,
                            dev=server.skynet,
                        )
                    except Exception as e:
                        logger.exception(e)
                        honeybadger.notify(e)
                        return
                elif (
                    "racket" in territory
                    and "racket" not in data["territory"][territoryid]
                ):
                    payload = {
                        "embeds": [
                            {
                                "title": "Racket Lost",
                                "description": f"A racket has been lost on {territoryid}, controlled by faction "
                                f'{data["name"]}. The racket was {data["territory"]["racket"]["name"]} '
                                f'and gave {territory["territory"]["racket"]["reward"]}.',
                                "timestamp": datetime.datetime.utcnow().isoformat(),
                                "footer": {"text": utils.torn_timestamp()},
                                "components": [
                                    {
                                        "type": 1,
                                        "components": [
                                            {
                                                "type": 2,
                                                "style": 5,
                                                "label": "Territory",
                                                "url": f"",
                                                "disabled": True,
                                            },
                                            {
                                                "type": 2,
                                                "style": 5,
                                                "label": "Faction",
                                                "url": f"https://www.torn.com/factions.php?step=profile&ID={data['ID']}",
                                            },
                                        ],
                                    }
                                ],
                            }
                        ]
                    }
                    try:
                        discordpost.delay(
                            f'channels/{guild_stakeout["channel"]}/messages',
                            payload=payload,
                            dev=server.skynet,
                        )
                    except Exception as e:
                        logger.exception(e)
                        honeybadger.notify(e)
                        return

            for territoryid, territory in data["territory"].items():
                if territoryid not in stakeout_data["territory"]:
                    payload = {
                        "embeds": [
                            {
                                "title": "Territory Gained",
                                "description": f"The territory {territoryid} has been claimed by "
                                f'faction {data["name"]}.',
                                "timestamp": datetime.datetime.utcnow().isoformat(),
                                "footer": {"text": utils.torn_timestamp()},
                                "components": [
                                    {
                                        "type": 1,
                                        "components": [
                                            {
                                                "type": 2,
                                                "style": 5,
                                                "label": "Territory",
                                                "url": f"",
                                                "disabled": True,
                                            },
                                            {
                                                "type": 2,
                                                "style": 5,
                                                "label": "Faction",
                                                "url": f"https://www.torn.com/factions.php?step=profile&ID={data['ID']}",
                                            },
                                        ],
                                    }
                                ],
                            }
                        ]
                    }
                    try:
                        discordpost.delay(
                            f'channels/{guild_stakeout["channel"]}/messages',
                            payload=payload,
                            dev=server.skynet,
                        )
                    except Exception as e:
                        logger.exception(e)
                        honeybadger.notify(e)
                        return
                if (
                    "racket" in territory
                    and "racket" not in stakeout_data["territory"][territoryid]
                ):
                    payload = {
                        "embeds": [
                            {
                                "title": "Racket Gained",
                                "description": f"A racket on {territoryid} has been controlled by faction "
                                f'{data["name"]}. The racket is '
                                f'{data["territory"]["racket"]["name"]} and '
                                f'gives {data["territory"]["racket"]["reward"]}.',
                                "timestamp": datetime.datetime.utcnow().isoformat(),
                                "footer": {"text": utils.torn_timestamp()},
                                "components": [
                                    {
                                        "type": 1,
                                        "components": [
                                            {
                                                "type": 2,
                                                "style": 5,
                                                "label": "Territory",
                                                "url": f"",
                                                "disabled": True,
                                            },
                                            {
                                                "type": 2,
                                                "style": 5,
                                                "label": "Faction",
                                                "url": f"https://www.torn.com/factions.php?step=profile&ID={data['ID']}",
                                            },
                                        ],
                                    }
                                ],
                            }
                        ]
                    }
                    try:
                        discordpost.delay(
                            f'channels/{guild_stakeout["channel"]}/messages',
                            payload=payload,
                            dev=server.skynet,
                        )
                    except Exception as e:
                        logger.exception(e)
                        honeybadger.notify(e)
                        return
                elif (
                    territory["racket"]["level"]
                    > stakeout_data["territory"][territoryid]["racket"]["level"]
                ):
                    payload = {
                        "embeds": [
                            {
                                "title": "Racket Leveled Up",
                                "description": f'A racket on {territoryid} controlled by faction {data["name"]}. '
                                f'The racket is {territory["racket"]["name"]} and now '
                                f'gives {territory["racket"]["reward"]} from '
                                f'{stakeout_data["territory"][territoryid]["racket"]["reward"]}.',
                                "timestamp": datetime.datetime.utcnow().isoformat(),
                                "footer": {"text": utils.torn_timestamp()},
                                "components": [
                                    {
                                        "type": 1,
                                        "components": [
                                            {
                                                "type": 2,
                                                "style": 5,
                                                "label": "Territory",
                                                "url": f"",
                                                "disabled": True,
                                            },
                                            {
                                                "type": 2,
                                                "style": 5,
                                                "label": "Faction",
                                                "url": f"https://www.torn.com/factions.php?step=profile&ID={data['ID']}",
                                            },
                                        ],
                                    }
                                ],
                            }
                        ]
                    }
                    try:
                        discordpost.delay(
                            f'channels/{guild_stakeout["channel"]}/messages',
                            payload=payload,
                            dev=server.skynet,
                        )
                    except Exception as e:
                        logger.exception(e)
                        honeybadger.notify(e)
                        return
                elif (
                    territory["racket"]["level"]
                    > stakeout_data["territory"][territoryid]["racket"]["level"]
                ):
                    payload = {
                        "embeds": [
                            {
                                "title": "Racket Leveled Down",
                                "description": f'A racket on {territoryid} controlled by faction {data["name"]}. '
                                f'The racket is {territory["racket"]["name"]} and now '
                                f'gives {territory["racket"]["reward"]} from '
                                f'{stakeout_data["territory"][territoryid]["racket"]["reward"]}.',
                                "timestamp": datetime.datetime.utcnow().isoformat(),
                                "footer": {"text": utils.torn_timestamp()},
                                "components": [
                                    {
                                        "type": 1,
                                        "components": [
                                            {
                                                "type": 2,
                                                "style": 5,
                                                "label": "Territory",
                                                "url": f"",
                                                "disabled": True,
                                            },
                                            {
                                                "type": 2,
                                                "style": 5,
                                                "label": "Faction",
                                                "url": f"https://www.torn.com/factions.php?step=profile&ID={data['ID']}",
                                            },
                                        ],
                                    }
                                ],
                            }
                        ]
                    }
                    try:
                        discordpost.delay(
                            f'channels/{guild_stakeout["channel"]}/messages',
                            payload=payload,
                            dev=server.skynet,
                        )
                    except Exception as e:
                        logger.exception(e)
                        honeybadger.notify(e)
                        return
        if (
            "members" in guild_stakeout["keys"]
            and data["members"] != stakeout_data["members"]
        ):
            for memberid, member in stakeout_data["members"].items():
                if memberid not in data["members"]:
                    payload = {
                        "embeds": [
                            {
                                "title": "Member Left",
                                "description": f'Member {member["name"]} has left faction {data["name"]}.',
                                "timestamp": datetime.datetime.utcnow().isoformat(),
                                "footer": {"text": utils.torn_timestamp()},
                                "components": [
                                    {
                                        "type": 1,
                                        "components": [
                                            {
                                                "type": 2,
                                                "style": 5,
                                                "label": "Member",
                                                "url": f"https://www.torn.com/profiles.php?XID={memberid}",
                                            },
                                            {
                                                "type": 2,
                                                "style": 5,
                                                "label": "Faction",
                                                "url": f"https://www.torn.com/factions.php?step=profile&ID={data['ID']}",
                                                "disabled": True,
                                            },
                                        ],
                                    }
                                ],
                            }
                        ]
                    }
                    try:
                        discordpost.delay(
                            f'channels/{guild_stakeout["channel"]}/messages',
                            payload=payload,
                            dev=server.skynet,
                        )
                    except Exception as e:
                        logger.exception(e)
                        honeybadger.notify(e)
                        return

            for memberid, member in data["members"].items():
                if memberid not in stakeout_data["members"]:
                    payload = {
                        "embeds": [
                            {
                                "title": "Member Joined",
                                "description": f'Member {member["name"]} has joined faction {data["name"]}.',
                                "timestamp": datetime.datetime.utcnow().isoformat(),
                                "footer": {"text": utils.torn_timestamp()},
                                "components": [
                                    {
                                        "type": 1,
                                        "components": [
                                            {
                                                "type": 2,
                                                "style": 5,
                                                "label": "Member",
                                                "url": f"https://www.torn.com/profiles.php?XID={memberid}",
                                            },
                                            {
                                                "type": 2,
                                                "style": 5,
                                                "label": "Faction",
                                                "url": f"https://www.torn.com/factions.php?step=profile&ID={data['ID']}",
                                                "disabled": True,
                                            },
                                        ],
                                    }
                                ],
                            }
                        ]
                    }
                    try:
                        discordpost.delay(
                            f'channels/{guild_stakeout["channel"]}/messages',
                            payload=payload,
                            dev=server.skynet,
                        )
                    except Exception as e:
                        logger.exception(e)
                        honeybadger.notify(e)
                        return
        if (
            "memberstatus" in guild_stakeout["keys"]
            and data["members"] != stakeout_data["members"]
        ):
            for memberid, member in stakeout_data["members"].items():
                if memberid not in data["members"]:
                    continue
                elif (
                    member["status"]["description"]
                    != data["members"][memberid]["status"]["description"]
                    or member["status"]["state"]
                    != data["members"][memberid]["status"]["state"]
                ):
                    if (
                        member["status"]["details"]
                        == data["members"][memberid]["status"]["details"]
                    ):
                        continue

                    payload = {
                        "embeds": [
                            {
                                "title": "Member Status Change",
                                "description": f'Member {member["name"]} of faction {data["name"]} is now '
                                f'{data["members"][memberid]["status"]["description"]} from '
                                f'{member["status"]["description"]}'
                                f'{"" if member["status"]["details"] == "" else " because " + utils.remove_html(member["status"]["details"])}.',
                                "timestamp": datetime.datetime.utcnow().isoformat(),
                                "footer": {"text": utils.torn_timestamp()},
                                "components": [
                                    {
                                        "type": 1,
                                        "components": [
                                            {
                                                "type": 2,
                                                "style": 5,
                                                "label": "Member",
                                                "url": f"https://www.torn.com/profiles.php?XID={memberid}",
                                            },
                                            {
                                                "type": 2,
                                                "style": 5,
                                                "label": "Faction",
                                                "url": f"https://www.torn.com/factions.php?step=profile&ID={data['ID']}",
                                                "disabled": True,
                                            },
                                        ],
                                    }
                                ],
                            }
                        ]
                    }
                    try:
                        discordpost.delay(
                            f'channels/{guild_stakeout["channel"]}/messages',
                            payload=payload,
                            dev=server.skynet,
                        )
                    except Exception as e:
                        logger.exception(e)
                        honeybadger.notify(e)
                        return
        if (
            "memberactivity" in guild_stakeout["keys"]
            and data["members"] != stakeout_data["members"]
        ):
            for memberid, member in stakeout_data["members"].items():
                if memberid not in data["members"]:
                    continue

                if (
                    member["last_action"]["status"] in ("Offline", "Idle")
                    and data["members"][memberid]["last_action"]["status"] == "Online"
                ):
                    if (
                        data["members"][memberid]["last_action"]["status"] == "Idle"
                        and datetime.datetime.now(datetime.timezone.utc).timestamp()
                        - data["members"][memberid]["last_action"]["timestamp"]
                        < 300
                    ):
                        continue

                    payload = {
                        "embeds": [
                            {
                                "title": "Member Activity Change",
                                "description": f'Member {member["name"]} of faction {data["name"]} is now '
                                f'{data["members"][memberid]["last_action"]["status"]} from '
                                f'{member["last_action"]["status"]}.',
                                "timestamp": datetime.datetime.utcnow().isoformat(),
                                "footer": {"text": utils.torn_timestamp()},
                                "components": [
                                    {
                                        "type": 1,
                                        "components": [
                                            {
                                                "type": 2,
                                                "style": 5,
                                                "label": "Member",
                                                "url": f"https://www.torn.com/profiles.php?XID={memberid}",
                                            },
                                            {
                                                "type": 2,
                                                "style": 5,
                                                "label": "Faction",
                                                "url": f"https://www.torn.com/factions.php?step=profile&ID={data['ID']}",
                                                "disabled": True,
                                            },
                                        ],
                                    }
                                ],
                            }
                        ]
                    }
                    try:
                        discordpost.delay(
                            f'channels/{guild_stakeout["channel"]}/messages',
                            payload=payload,
                            dev=server.skynet,
                        )
                    except Exception as e:
                        logger.exception(e)
                        honeybadger.notify(e)
                        return
                elif member["last_action"]["status"] in ("Online", "Idle") and data[
                    "members"
                ][memberid]["last_action"]["status"] in ("Offline", "Idle"):
                    if (
                        data["members"][memberid]["last_action"]["status"] == "Idle"
                        and datetime.datetime.now(datetime.timezone.utc).timestamp()
                        - data["members"][memberid]["last_action"]["timestamp"]
                        < 300
                    ):
                        continue
                    elif (
                        data["members"][memberid]["last_action"]["status"] == "Idle"
                        and member["last_action"]["status"] == "Idle"
                    ):
                        continue

                    payload = {
                        "embeds": [
                            {
                                "title": "Member Activity Change",
                                "description": f'Member {member["name"]} of faction {data["name"]} is now '
                                f'{data["members"][memberid]["last_action"]["status"]} from '
                                f'{member["last_action"]["status"]}.',
                                "timestamp": datetime.datetime.utcnow().isoformat(),
                                "footer": {"text": utils.torn_timestamp()},
                                "components": [
                                    {
                                        "type": 1,
                                        "components": [
                                            {
                                                "type": 2,
                                                "style": 5,
                                                "label": "Member",
                                                "url": f"https://www.torn.com/profiles.php?XID={memberid}",
                                            },
                                            {
                                                "type": 2,
                                                "style": 5,
                                                "label": "Faction",
                                                "url": f"https://www.torn.com/factions.php?step=profile&ID={data['ID']}",
                                                "disabled": True,
                                            },
                                        ],
                                    }
                                ],
                            }
                        ]
                    }
                    try:
                        discordpost.delay(
                            f'channels/{guild_stakeout["channel"]}/messages',
                            payload=payload,
                            dev=server.skynet,
                        )
                    except Exception as e:
                        logger.exception(e)
                        honeybadger.notify(e)
                        return
        if (
            "assault" in guild_stakeout["keys"]
            and data["territory_wars"] != stakeout_data["territory_wars"]
        ):
            for war in data["territory_wars"]:
                existing = False

                for old_war in stakeout_data["territory_wars"]:
                    if old_war["territory"] == war["territory"]:
                        existing = True
                        break

                if not existing:
                    defending = FactionModel.objects(
                        tid=war["defending_faction"]
                    ).first()
                    assaulting = FactionModel.objects(
                        tid=war["assaulting_faction"]
                    ).first()

                    payload = {
                        "embeds": [
                            {
                                "title": "Territory Assaulted",
                                "description": f'Territory {war["territory"]} of faction '
                                f'{war["defending_faction"] if defending is None else defending.name}'
                                f" has been assaulted by faction "
                                f'{war["assaulting_faction"] if assaulting is None else assaulting.name}.',
                                "timestamp": datetime.datetime.fromtimestamp(
                                    war["start_time"]
                                ).isoformat(),
                                "footer": {
                                    "text": utils.torn_timestamp(war["start_time"])
                                },
                                "components": [
                                    {
                                        "type": 1,
                                        "components": [
                                            {
                                                "type": 2,
                                                "style": 5,
                                                "label": "Territory",
                                                "url": f"",
                                                "disabled": True,
                                            },
                                            {
                                                "type": 2,
                                                "style": 5,
                                                "label": "Faction",
                                                "url": f"https://www.torn.com/factions.php?step=profile&ID={data['ID']}",
                                            },
                                        ],
                                    }
                                ],
                            }
                        ]
                    }
                    try:
                        discordpost.delay(
                            f'channels/{guild_stakeout["channel"]}/messages',
                            payload=payload,
                            dev=server.skynet,
                        )
                    except Exception as e:
                        logger.exception(e)
                        honeybadger.notify(e)
                        return
            for war in stakeout_data["territory_wars"]:
                existing = False

                for new_war in data["territory_wars"]:
                    if new_war["territory"] == war["territory"]:
                        existing = True
                        break

                if not existing:
                    defending = FactionModel.objects(
                        tid=war["defending_faction"]
                    ).first()
                    assaulting = FactionModel.objects(
                        tid=war["assaulting_faction"]
                    ).first()
                    payload = {
                        "embeds": [
                            {
                                "title": "Territory Assault Ended",
                                "description": f'The assault of territory {war["territory"]} of faction '
                                f'{war["defending_faction"] if defending is None else defending.name}'
                                f" by faction "
                                f'{war["assaulting_faction"] if assaulting is None else assaulting.name}.'
                                f"has ended.",
                                "timestamp": datetime.datetime.utcnow().isoformat(),
                                "footer": {"text": utils.torn_timestamp()},
                                "components": [
                                    {
                                        "type": 1,
                                        "components": [
                                            {
                                                "type": 2,
                                                "style": 5,
                                                "label": "Territory",
                                                "url": f"",
                                                "disabled": True,
                                            },
                                            {
                                                "type": 2,
                                                "style": 5,
                                                "label": "Faction",
                                                "url": f"https://www.torn.com/factions.php?step=profile&ID={data['ID']}",
                                            },
                                        ],
                                    }
                                ],
                            }
                        ]
                    }
                    try:
                        discordpost.delay(
                            f'channels/{guild_stakeout["channel"]}/messages',
                            payload=payload,
                            dev=server.skynet,
                        )
                    except Exception as e:
                        logger.exception(e)
                        honeybadger.notify(e)
                        return
        if "armory" in guild_stakeout["keys"]:
            server = ServerModel.objects(sid=guildid).first()
            faction = FactionModel.objects(tid=stakeout.tid).first()

            if stakeout.tid in server.factions and faction.guild == int(guildid):
                try:
                    if key is not None:
                        data = tornget(
                            f"faction/{stakeout.tid}?selections=armorynews",
                            key=key,
                            session=requests_session,
                            fromts=utils.now() - 60,
                        )
                    else:
                        keys = UserModel.objects(
                            Q(factionaa=True) & Q(factionid=faction.tid)
                        )

                        if len(keys) == 0:
                            break

                        data = tornget(
                            f"faction/{stakeout.tid}?selections=armorynews",
                            key=random.choice(keys.key),
                            session=requests_session,
                            fromts=utils.now() - 60,
                        )
                except utils.TornError as e:
                    logger.exception(e)
                    honeybadger.notify(
                        e, context={"code": e.code, "endpoint": e.endpoint}
                    )
                    return
                except Exception as e:
                    logger.exception(e)
                    honeybadger.notify(e)
                    break

                if len(data["armorynews"]) == 0:
                    break

                for news in data["armorynews"].values():
                    timestamp = news["timestamp"]
                    news = utils.remove_html(news["news"])

                    if any(
                        word in news.lower()
                        for word in ["loaned", "returned", "retrieved"]
                    ):
                        payload = {
                            "embeds": [
                                {
                                    "title": "Armory Change",
                                    "description": news,
                                    "timestamp": datetime.datetime.utcnow().isoformat(),
                                    "footer": {"text": utils.torn_timestamp(timestamp)},
                                }
                            ]
                        }

                        try:
                            discordpost.delay(
                                f'channels/{guild_stakeout["channel"]}/messages',
                                payload=payload,
                                dev=server.skynet,
                            )
                        except Exception as e:
                            logger.exception(e)
                            honeybadger.notify(e)
                            return
        if "armorydeposit" in guild_stakeout["keys"]:
            server = ServerModel.objects(sid=guildid).first()
            faction = FactionModel.objects(tid=stakeout.tid).first()
            if stakeout.tid in server.factions and faction.guild == int(guildid):
                try:
                    if key is not None:
                        data = tornget(
                            f"faction/{stakeout.tid}?selections=armorynews",
                            key=key,
                            session=requests_session,
                            fromts=utils.now() - 60,
                        )
                    else:
                        aa_users = UserModel.objects(
                            Q(factionaa=True) & Q(factionid=faction.tid)
                        )
                        keys = []

                        user: UserModel
                        for user in aa_users:
                            if user.key == "":
                                user.factionaa = False
                                user.save()
                                continue

                            keys.append(user.key)

                        keys = list(set(keys))

                        if len(keys) == 0:
                            break

                        data = tornget(
                            f"faction/{stakeout.tid}?selections=armorynews",
                            key=random.choice(keys),
                            session=requests_session,
                            fromts=utils.now() - 60,
                        )
                except utils.TornError as e:
                    logger.exception(e)
                    honeybadger.notify(
                        e, context={"code": e.code, "endpoint": e.endpoint}
                    )
                    return
                except Exception as e:
                    logger.exception(e)
                    honeybadger.notify(e)
                    break

                if len(data["armorynews"]) == 0:
                    break

                for news in data["armorynews"].values():
                    timestamp = news["timestamp"]
                    news = utils.remove_html(news["news"])

                    if any(word in news.lower() for word in ["deposited"]):
                        payload = {
                            "embeds": [
                                {
                                    "title": "Armory Deposit",
                                    "description": news,
                                    "timestamp": datetime.datetime.utcnow().isoformat(),
                                    "footer": {"text": utils.torn_timestamp(timestamp)},
                                }
                            ]
                        }

                        try:
                            discordpost.delay(
                                f'channels/{guild_stakeout["channel"]}/messages',
                                payload=payload,
                                dev=server.skynet,
                            )
                        except Exception as e:
                            logger.exception(e)
                            honeybadger.notify(e)
                            return
