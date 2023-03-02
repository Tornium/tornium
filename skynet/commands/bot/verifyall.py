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

from tornium_commons.skyutils import SKYNET_ERROR

from skynet.skyutils import invoker_exists


@invoker_exists
def verifyall(interaction, *args, **kwargs):
    return {
        "type": 4,
        "data": {
            "embeds": [
                {
                    "title": "Command Disabled",
                    "description": "This command has been disabled pending re-implemenation.",
                    "color": SKYNET_ERROR,
                }
            ],
            "flags": 64,  # Ephemeral
        },
    }

    # print(interaction)
    #
    # if "guild_id" not in interaction:
    #     return {
    #         "type": 4,
    #         "data": {
    #             "embeds": [
    #                 {
    #                     "title": "Invalid Location",
    #                     "description": "The verification command must be run in a server where verification is setup "
    #                     "and enabled.",
    #                 }
    #             ],
    #             "flags": 64,  # Ephemeral
    #         },
    #     }
    #
    # server = Server(interaction["guild_id"])
    #
    # if server.config.get("verify") in (None, 0):
    #     return {
    #         "type": 4,
    #         "data": {
    #             "embeds": [
    #                 {
    #                     "title": "Verification Not Enabled",
    #                     "description": "Verification is not enabled in the server's admin dashboard.",
    #                     "color": SKYNET_ERROR,
    #                 }
    #             ],
    #             "flags": 64,  # Ephemeral
    #         },
    #     }
    # elif server.verify_template == "" and len(server.verified_roles) == 0 and len(server.faction_verify) == 0:
    #     return {
    #         "type": 4,
    #         "data": {
    #             "embeds": [
    #                 {
    #                     "title": "Verification Not Enabled",
    #                     "description": "Verification is enabled, but nothing will be changed based on the current "
    #                     "settings in the server's admin dashboard.",
    #                     "color": SKYNET_ERROR,
    #                 }
    #             ],
    #             "flags": 64,  # Ephemeral
    #         },
    #     }
    # elif kwargs["invoker"].tid not in server.admins:
    #     return {
    #         "type": 4,
    #         "data": {
    #             "embeds": [
    #                 {
    #                     "title": "Permission Denied",
    #                     "description": "Only server admins are allowed to run this command",
    #                     "color": SKYNET_ERROR,
    #                 }
    #             ],
    #             "flags": 64,  # Ephemeral
    #         },
    #     }
    #
    # if "options" in interaction["data"]:
    #     force = utils.find_list(interaction["data"]["options"], "name", "force")
    # else:
    #     force = -1
    #
    # admin_keys = kwargs.get("admin_keys")
    #
    # if admin_keys is None:
    #     admin_keys = get_admin_keys(interaction)
    #
    # if len(admin_keys) == 0:
    #     return {
    #         "type": 4,
    #         "data": {
    #             "embeds": [
    #                 {
    #                     "title": "No API Keys",
    #                     "description": "No API keys were found to be run for this command. Please sign into "
    #                     "Tornium or run this command in a server with signed-in admins.",
    #                     "color": SKYNET_ERROR,
    #                 }
    #             ],
    #             "flags": 64,  # Ephemeral
    #         },
    #     }
    #
    # # requests.exceptions.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
    # # try:
    # #     tasks.discordpost(
    # #         f"interactions/{interaction['id']}/{interaction['token']}/callback",
    # #         payload={
    # #             "type": 5
    # #         },
    # #     )
    # # except utils.DiscordError as e:
    # #     return {
    # #         "type": 4,
    # #         "data": {
    # #             "embeds": [
    # #                 {
    # #                     "title": "Discord API Error",
    # #                     "description": f'The Discord API has raised error code {e.code}: "{e.message}".',
    # #                     "color": 0xC83F49,
    # #                 }
    # #             ],
    # #             "flags": 64,  # Ephemeral
    # #         },
    # #     }
    # # except utils.NetworkingError as e:
    # #     return {
    # #         "type": 4,
    # #         "data": {
    # #             "embeds": [
    # #                 {
    # #                     "title": "HTTP Error",
    # #                     "description": f'The Discord API has returned an HTTP error {e.code}: "{e.message}".',
    # #                     "color": 0xC83F49,
    # #                 }
    # #             ],
    # #             "flags": 64,  # Ephemeral
    # #         },
    # #     }
    #
    # try:
    #     server_data = tornium_celery.tasks.api.discordget(
    #         f"guilds/{server.sid}?with_counts=true",
    #         bucket=f"guilds/{server.sid}",
    #         retry=True,
    #     )
    # except utils.DiscordError as e:
    #     return {
    #         "type": 4,
    #         "data": {
    #             "embeds": [
    #                 {
    #                     "title": "Discord API Error",
    #                     "description": f'The Discord API has raised error code {e.code}: "{e.message}".',
    #                     "color": SKYNET_ERROR,
    #                 }
    #             ],
    #             "flags": 64,  # Ephemeral
    #         },
    #     }
    # except utils.NetworkingError as e:
    #     return {
    #         "type": 4,
    #         "data": {
    #             "embeds": [
    #                 {
    #                     "title": "HTTP Error",
    #                     "description": f'The Discord API has returned an HTTP error {e.code}: "{e.message}".',
    #                     "color": SKYNET_ERROR,
    #                 }
    #             ],
    #             "flags": 64,  # Ephemeral
    #         },
    #     }
    #
    # member_count = 0
    # member_fetch_run = 0
    # errors = 0
    # log_channel_found = False
    #
    # for category in server.get_text_channels().values():
    #     if str(server.verify_log_channel) in category["channels"]:
    #         log_channel_found = True
    #         break
    #
    # while (
    #     member_count <= server_data["approximate_member_count"] * 0.99
    #     and member_fetch_run < (server_data["approximate_member_count"] // 1000 + 1)
    #     and member_fetch_run < 100
    # ):
    #     try:
    #         guild_members = tornium_celery.tasks.api.discordget(
    #             f"guilds/{server.sid}/members?limit=1000",
    #             bucket=f"guilds/{server.sid}",
    #             retry=True,
    #         )
    #     except utils.DiscordError as e:
    #         return {
    #             "type": 4,
    #             "data": {
    #                 "embeds": [
    #                     {
    #                         "title": "Discord API Error",
    #                         "description": f'The Discord API has raised error code {e.code}: "{e.message}".',
    #                         "color": SKYNET_ERROR,
    #                     }
    #                 ],
    #                 "flags": 64,  # Ephemeral
    #             },
    #         }
    #     except utils.NetworkingError as e:
    #         return {
    #             "type": 4,
    #             "data": {
    #                 "embeds": [
    #                     {
    #                         "title": "HTTP Error",
    #                         "description": f'The Discord API has returned an HTTP error {e.code}: "{e.message}".',
    #                         "color": 0xC83F49,
    #                     }
    #                 ],
    #                 "flags": 64,  # Ephemeral
    #             },
    #         }
    #
    #     for guild_member in guild_members:
    #         if "user" not in guild_member:
    #             continue
    #
    #         user: UserModel = UserModel.objects(discord_id=guild_member["user"]["id"]).first()
    #
    #         if user is None:
    #             try:
    #                 user_data = tornium_celery.tasks.api.tornget(
    #                     f"user/{guild_member['user']['id']}?selections=profile,discord",
    #                     random.choice(admin_keys),
    #                 )
    #             except utils.TornError as e:
    #                 errors += 1
    #
    #                 if server.verify_log_channel in (None, 0):
    #                     continue
    #
    #                 if e.code == 6:
    #                     errors -= 1
    #                     payload = {
    #                         "embeds": [
    #                             {
    #                                 "title": "API Verification Failed",
    #                                 "description": f"<@{guild_member['user']['id']}> is not officially verified by Torn.",
    #                                 "color": 0xC83F49,
    #                                 "author": {
    #                                     "name": guild_member["nick"]
    #                                     if "nick" in guild_member
    #                                     else guild_member["user"]["username"],
    #                                     "url": f"https://discordapp.com/users/{guild_member['user']['id']}",
    #                                     "icon_url": f"https://cdn.discordapp.com/avatars/{guild_member['user']['id']}/"
    #                                     f"{guild_member['user']['avatar']}.webp",
    #                                 },
    #                             }
    #                         ]
    #                     }
    #                 else:
    #                     payload = {
    #                         "embeds": [
    #                             {
    #                                 "title": "Torn API Error",
    #                                 "description": f'The Torn API has raised error code {e.code}: "{e.message}".',
    #                                 "color": 0xC83F49,
    #                                 "footer": {"text": f"Failed on member <@{guild_member['user']['id']}>"},
    #                             }
    #                         ]
    #                     }
    #
    #                 if log_channel_found:
    #                     tornium_celery.tasks.api.discordpost.delay(
    #                         f"channels/{server.verify_log_channel}/messages",
    #                         payload=payload,
    #                         bucket=f"channels/{server.verify_log_channel}",
    #                         retry=True,
    #                     )
    #                 continue
    #             except utils.NetworkingError as e:
    #                 errors += 1
    #
    #                 if server.verify_log_channel in (None, 0):
    #                     continue
    #
    #                 payload = {
    #                     "embeds": [
    #                         {
    #                             "title": "HTTP Error",
    #                             "description": f'The Torn API has returned an HTTP error {e.code}: "{e.message}".',
    #                             "color": 0xC83F49,
    #                             "footer": {"text": f"Failed on member <@{guild_member['user']['id']}>"},
    #                         }
    #                     ],
    #                 }
    #
    #                 if log_channel_found:
    #                     tornium_celery.tasks.api.discordpost.delay(
    #                         f"channels/{server.verify_log_channel}/messages",
    #                         payload=payload,
    #                         bucket=f"channels/{server.verify_log_channel}",
    #                         retry=True,
    #                     )
    #                 continue
    #
    #             user: UserModel = UserModel.objects(tid=user_data["player_id"]).modify(
    #                 upsert=True,
    #                 new=True,
    #                 set__name=user_data["name"],
    #                 set__level=user_data["level"],
    #                 set__last_refresh=utils.now(),
    #                 set__discord_id=user_data["discord"]["discordID"] if user_data["discord"]["discordID"] != "" else 0,
    #                 set__factionid=user_data["faction"]["faction_id"],
    #                 set__status=user_data["last_action"]["status"],
    #                 set__last_action=user_data["last_action"]["timestamp"],
    #             )
    #         elif user.tid == 0:
    #             payload = {
    #                 "embeds": [
    #                     {
    #                         "title": "API Verification Failed",
    #                         "description": f"<@{guild_member['user']['id']}> is not officially verified by Torn.",
    #                         "color": 0xC83F49,
    #                         "author": {
    #                             "name": guild_member["nick"]
    #                             if "nick" in guild_member
    #                             else guild_member["user"]["username"],
    #                             "url": f"https://discordapp.com/users/{guild_member['user']['id']}",
    #                             "icon_url": f"https://cdn.discordapp.com/avatars/{guild_member['user']['id']}/"
    #                             f"{guild_member['user']['avatar']}.webp",
    #                         },
    #                     }
    #                 ]
    #             }
    #
    #             if log_channel_found:
    #                 tornium_celery.tasks.api.discordpost.delay(
    #                     f"channels/{server.verify_log_channel}/messages",
    #                     payload=payload,
    #                     bucket=f"channels/{server.verify_log_channel}",
    #                     retry=True,
    #                 )
    #             continue
    #
    #         try:
    #             user: User = User(user.tid)
    #             user.refresh(key=random.choice(admin_keys), force=True if force != -1 else False)
    #         except utils.MissingKeyError:
    #             errors += 1
    #             continue
    #
    #         if user.discord_id in (0, None):
    #             if server.verify_log_channel in (None, 0):
    #                 continue
    #
    #             payload = {
    #                 "embeds": [
    #                     {
    #                         "title": "API Verification Failed",
    #                         "description": f"<@{guild_member['user']['id']}> is not officially verified by Torn.",
    #                         "color": 0xC83F49,
    #                         "author": {
    #                             "name": guild_member["nick"]
    #                             if "nick" in guild_member
    #                             else guild_member["user"]["username"],
    #                             "url": f"https://discordapp.com/users/{guild_member['user']['id']}",
    #                             "icon_url": f"https://cdn.discordapp.com/avatars/{guild_member['user']['id']}/"
    #                             f"{guild_member['user']['avatar']}.webp",
    #                         },
    #                     }
    #                 ]
    #             }
    #
    #             if log_channel_found:
    #                 tornium_celery.tasks.api.discordpost.delay(
    #                     f"channels/{server.verify_log_channel}/messages",
    #                     payload=payload,
    #                     bucket=f"channels/{server.verify_log_channel}",
    #                     retry=True,
    #                 )
    #             continue
    #
    #         patch_json = {}
    #
    #         if server.verify_template != "":
    #             nick = (
    #                 jinja2.Environment(autoescape=True)
    #                 .from_string(server.verify_template)
    #                 .render(name=user.name, tid=user.tid, tag="")
    #             )
    #
    #             if "nick" in guild_member and nick != guild_member["nick"] and nick != guild_member["user"]["username"]:
    #                 patch_json["nick"] = nick
    #
    #         if len(server.verified_roles) != 0 and user.discord_id != 0:
    #             verified_role: int
    #             for verified_role in server.verified_roles:
    #                 if str(verified_role) in guild_member["roles"]:
    #                     continue
    #                 elif patch_json.get("roles") is None or len(patch_json["roles"]) == 0:
    #                     patch_json["roles"] = guild_member["roles"]
    #
    #                 patch_json["roles"].append(str(verified_role))
    #         elif user.discord_id == 0 and len(server.verified_roles) != 0:
    #             verified_role: int
    #             for verified_role in server.verified_roles:
    #                 if str(verified_role) in guild_member["roles"]:
    #                     if patch_json.get("roles") is None or len(patch_json["roles"]) == 0:
    #                         patch_json["roles"] = guild_member["roles"]
    #
    #                     patch_json["roles"].remove(str(verified_role))
    #
    #         if (
    #             server.faction_verify.get(str(user.factiontid)) is not None
    #             and server.faction_verify[str(user.factiontid)].get("roles") is not None
    #             and len(server.faction_verify[str(user.factiontid)]["roles"]) != 0
    #             and server.faction_verify[str(user.factiontid)].get("enabled") not in (None, False)
    #         ):
    #             faction_role: int
    #             for faction_role in server.faction_verify[str(user.factiontid)]["roles"]:
    #                 if str(faction_role) in guild_member["roles"]:
    #                     continue
    #                 elif patch_json.get("roles") is None or len(patch_json["roles"]) == 0:
    #                     patch_json["roles"] = guild_member["roles"]
    #
    #                 patch_json["roles"].append(str(faction_role))
    #
    #         for factiontid, data in server.faction_verify.items():
    #             for faction_role in server.faction_verify[str(factiontid)]["roles"]:
    #                 if str(faction_role) in guild_member["roles"] and int(factiontid) != user.factiontid:
    #                     if patch_json.get("roles") is None or len(patch_json["roles"]) == 0:
    #                         patch_json["roles"] = guild_member["roles"]
    #
    #                     patch_json["roles"].remove(str(faction_role))
    #
    #         if len(patch_json) == 0 and (force == -1 or (type(force) == list and not force[1].get("value"))):
    #             continue
    #
    #         if "roles" in patch_json:
    #             patch_json["roles"] = list(set(patch_json["roles"]))
    #
    #         print(patch_json)
    #
    #         tornium_celery.tasks.api.discordpatch.delay(
    #             f"guilds/{server.sid}/members/{user.discord_id}",
    #             patch_json,
    #             bucket=f"guilds/{server.sid}",
    #             retry=True,
    #         )
    #
    #         payload = {
    #             "embeds": [
    #                 {
    #                     "title": "API Verification Attempted",
    #                     "description": f"<@{guild_member['user']['id']}> is officially verified by Torn with updated "
    #                     f"roles and nickname.",
    #                     "color": SKYNET_GOOD,
    #                     "author": {
    #                         "name": guild_member["nick"]
    #                         if "nick" in guild_member
    #                         else guild_member["user"]["username"],
    #                         "url": f"https://discordapp.com/users/{guild_member['user']['id']}",
    #                         "icon_url": f"https://cdn.discordapp.com/avatars/{guild_member['user']['id']}/"
    #                         f"{guild_member['user']['avatar']}.webp",
    #                     },
    #                 }
    #             ]
    #         }
    #
    #         if log_channel_found:
    #             tornium_celery.tasks.api.discordpost.delay(
    #                 f"channels/{server.verify_log_channel}/messages",
    #                 payload=payload,
    #                 bucket=f"channels/{server.verify_log_channel}",
    #                 retry=True,
    #             )
    #         continue
    #
    #     member_count += len(guild_members)
    #     member_fetch_run += 1
    #
    # return {
    #     "type": 4,
    #     "data": {
    #         "embeds": [
    #             {
    #                 "title": "Verification Complete",
    #                 "description": f"Approximately {server_data['approximate_member_count']}; Accurately {member_count}",
    #             }
    #         ]
    #     },
    # }
