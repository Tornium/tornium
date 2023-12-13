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

# import inspect
# import random
# import time
# import typing
#
# from tornium_celery.tasks.user import update_user
# from tornium_commons.formatters import HumanTimeDelta, commas, find_list, rel_time
# from tornium_commons.models import PersonalStats, User
# from tornium_commons.skyutils import SKYNET_ERROR


def user_who(interaction, *args, **kwargs):
    return {
        "type": 4,
        "data": {
            "content": "This feature is in the progress of being rewritten. Please check back later.",
            "flags": 64,
        },
    }


# def user_who(interaction, *args, **kwargs):
#     if "options" in interaction["data"]:
#         user_mention = find_list(interaction["data"]["options"], "name", "user")
#         user_tid = find_list(interaction["data"]["options"], "name", "tid")
#     else:
#         user_mention = -1
#         user_tid = -1
#
#     user: User = kwargs["invoker"]
#
#     if user_mention != -1 and user_tid != -1:
#         return {
#             "type": 4,
#             "data": {
#                 "embeds": [
#                     {
#                         "title": "Invalid User",
#                         "description": "You need to select either a user ID/name or a user mention, not both.",
#                         "color": SKYNET_ERROR,
#                     }
#                 ],
#                 "flags": 64,
#             },
#         }
#
#     mentioned_user: typing.Optional[User]
#     if user_mention != -1:
#         user_query_str = f"<@{user_mention[1]['value']}>"
#         mentioned_user = UserModel.objects(discord_id=int(user_mention[1]["value"])).first()
#     elif user_tid != -1:
#         if user_tid[1]["value"].isdigit():
#             user_query_str = f"Torn ID {user_tid[1]['value']}"
#             mentioned_user = UserModel.objects(tid=int(user_tid[1]["value"])).first()
#         else:
#             user_query_str = f"Torn name {user_tid[1]['value']}"
#             mentioned_user = UserModel.objects(name__iexact=user_tid[1]["value"]).first()
#     else:
#         user_query_str = f"Torn user {user.name} [{user.tid}]"
#         mentioned_user = user
#
#     if time.time() - mentioned_user.last_refresh > 86400:  # One day
#         admin_keys: tuple = kwargs["admin_keys"]
#
#         if len(admin_keys) == 0:
#             return {
#                 "type": 4,
#                 "data": {
#                     "embeds": [
#                         {
#                             "title": "No API Keys",
#                             "description": "No API keys were found to be run for this command. Please sign into "
#                             "Tornium or run this command in a server with signed-in admins.",
#                             "color": SKYNET_ERROR,
#                         }
#                     ],
#                     "flags": 64,  # Ephemeral
#                 },
#             }
#
#         update_user_kwargs = {
#             "key": random.choice(admin_keys),
#             "refresh_existing": True,
#         }
#
#         if user_mention != -1:
#             update_user_kwargs["discordid"] = int(user_mention[1]["value"])
#         elif user_tid != -1:
#             update_user_kwargs["tid"] = int(user_tid[1]["value"])
#         else:
#             update_user_kwargs["tid"] = user.tid
#
#         try:
#             update_user(**update_user_kwargs)
#         except Exception as e:
#             print(e)
#             return {
#                 "type": 4,
#                 "data": {
#                     "embeds": [
#                         {
#                             "title": "Backend Exception",
#                             "description": "There has been an error raised on the backend. This error has been logged "
#                             "by the backend. Please try again or contact the developer if this issue "
#                             "continue occurring.",
#                             "color": SKYNET_ERROR,
#                         }
#                     ],
#                     "flags": 64,
#                 },
#             }
#
#         mentioned_user.reload()
#
#     if mentioned_user is None:
#         return {
#             "type": 4,
#             "data": {
#                 "embeds": [
#                     {
#                         "title": "Unknown User",
#                         "description": f"{user_query_str} could not be located in the user database or via the Torn API.",
#                         "color": SKYNET_ERROR,
#                     }
#                 ],
#                 "flags": 64,
#             },
#         }
#
#     ps: typing.Optional[PersonalStatModel] = (
#         PersonalStatModel.objects(tid=mentioned_user.tid).order_by("-timestamp").first()
#     )
#     payload = {
#         "type": 4,
#         "data": {
#             "embeds": [
#                 {
#                     "title": f"{mentioned_user.name} [{mentioned_user.tid}]",
#                     "footer": {"text": f"Last Update: {rel_time(mentioned_user.last_refresh)}"},
#                 }
#             ],
#             "components": [
#                 {
#                     "type": 1,
#                     "components": [
#                         {
#                             "type": 2,
#                             "style": 5,
#                             "label": "Profile",
#                             "url": f"https://www.torn.com/profiles.php?XID={mentioned_user.tid}",
#                         },
#                         {
#                             "type": 2,
#                             "style": 5,
#                             "label": "Attack",
#                             "url": f"https://www.torn.com/loader.php?sid=attack&user2ID={mentioned_user.tid}",
#                         },
#                     ],
#                 }
#             ],
#             "flags": 64,
#         },
#     }
#
#     if mentioned_user.factionid != 0:
#         payload["data"]["components"].append(
#             {
#                 "type": 1,
#                 "components": [
#                     {
#                         "type": 2,
#                         "style": 5,
#                         "label": "Faction",
#                         "url": f"https://www.torn.com/factions.php?step=profile&ID={mentioned_user.factionid}",
#                     }
#                 ],
#             }
#         )
#
#     if ps is None:
#         payload["data"]["embeds"][0]["description"] = inspect.cleandoc(
#             f"""Level {mentioned_user.level} - Title (NYI)
#             Life NYI/NYI
#             Last online: {rel_time(mentioned_user.last_action)}
#             """
#         )
#         payload["data"]["embeds"][0]["fields"] = [
#             {"name": "Faction", "value": "NYI", "inline": True},
#             {
#                 "name": "Company",
#                 "value": "NYI",
#                 "inline": True,
#             },
#         ]
#     else:
#         payload["data"]["embeds"][0]["description"] = inspect.cleandoc(
#             f"""Level {mentioned_user.level} - Title (NYI)
#             Life NYI/NYI
#             Last online: {rel_time(mentioned_user.last_action)}
#             Playtime: {str(HumanTimeDelta(seconds=ps.useractivity))}
#             """
#         )
#         payload["data"]["embeds"].append(
#             {
#                 "title": "User Personal Stats",
#                 "fields": [
#                     {
#                         "name": "Activity",
#                         "value": inspect.cleandoc(
#                             f"""Playtime: {str(HumanTimeDelta(seconds=ps.useractivity))}
#                             Activity Streak: {commas(ps.activestreak)}"""
#                         ),
#                         "inline": True,
#                     },
#                     {
#                         "name": "Attacks",
#                         "value": inspect.cleandoc(
#                             f"""Attacks won: {commas(ps.attackswon)}
#                             Defends won: {commas(ps.defendswon)}
#                             ELO: {commas(ps.elo)}
#                             Retals: {commas(ps.retals)}
#                             TT clears: {commas(ps.territoryclears)}
#                             RW hits: {commas(ps.rankedwarhits)}"""
#                         ),
#                         "inline": True,
#                     },
#                     {
#                         "name": "Training",
#                         "value": inspect.cleandoc(
#                             f"""Xanax used: {commas(ps.xantaken)}
#                             Extasy used: {commas(ps.exttaken)}
#                             Refills used: {commas(ps.refills)}
#                             E-cans used: {commas(ps.energydrinkused)}
#                             SEs used: {commas(ps.statenhancersused)}"""
#                         ),
#                         "inline": True,
#                     },
#                     {
#                         "name": "Misc.",
#                         "value": inspect.cleandoc(
#                             f"""Revives done: {commas(ps.revives)}
#                             Revive skill: {ps.reviveskill}
#
#                             Networth: ${commas(ps.networth)}
#
#                             Nerve refills: {commas(ps.nerverefills)}
#                             Alcohol used: {commas(ps.alcoholused)}"""
#                         ),
#                         "inline": True,
#                     },
#                 ],
#                 "footer": {
#                     "text": f"Last Update: {rel_time(ps.timestamp)}",
#                 },
#             }
#         )
#
#     return payload
