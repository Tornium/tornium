# This file is part of Tornium.
#
# Tornium is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tornium is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Tornium.  If not, see <https://www.gnu.org/licenses/>.

import asyncio
import datetime
import logging
import random
from urllib.parse import urlparse, parse_qs

import discord
from discord.ext import commands
import honeybadger
from mongoengine import connect

from redisdb import get_redis
import settings  # Do not remove - initializes redis values

redis = get_redis()
honeybadger.honeybadger.configure(api_key=redis.get('tornium:settings:honeykey'))

connect(
    db='Tornium',
    username=redis.get('tornium:settings:username'),
    password=redis.get('tornium:settings:password'),
    host=f'mongodb://{redis.get("tornium:settings:host")}',
    connect=False
)

from bot import botutils
from bot.periodic import Periodic
from bot.vault import Vault
from models.factionmodel import FactionModel
from models.server import Server
from models.servermodel import ServerModel
from models.user import User
from models.usermodel import UserModel
import tasks
import utils

botlogger = logging.getLogger('bot')
botlogger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='bot.log', encoding='utf-8', mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
botlogger.addHandler(handler)

client = discord.client.Client()
intents = discord.Intents.all()

bot = commands.Bot(command_prefix=botutils.get_prefix, help_command=None, intents=intents)


@bot.event
async def on_ready():
    guild_count = 0

    for guild in bot.guilds:
        print(f"- {guild.id} (name: {guild.name})")
        guild_count += 1

    print(f'Bot is in {guild_count} guilds.')

    bot.add_cog(Periodic(bot, botlogger))
    bot.add_cog(Vault(bot, botlogger))


@bot.event
async def on_guild_join(guild):
    server = ServerModel(
        sid=guild.id,
        name=guild.name,
        admins=[],
        prefix='?',
        config={
            'stakeouts': 0,
            'assists': 0
        },
        factions=[],
        stakeoutconfig={
            'category': 0
        },
        userstakeouts=[],
        factionstakeouts=[],
        assistschannel=0
    )

    for member in guild.members:
        if member.guild_permissions.administrator:
            user = utils.first(UserModel.objects(discord_id=member.id))
            if user is None:
                continue

            user.servers.append(str(guild.id))
            server.admins.append(user.tid)

            user.servers = list(set(user.servers))
            server.admins = list(set(server.admins))
            user.save()

    server.save()


@bot.event
async def on_guild_remove(guild):
    server = utils.first(ServerModel.objects(sid=guild.id))
    if server is not None:
        for admin in server.admins:
            user = utils.first(UserModel.objects(tid=admin))
            if user is not None:
                user.servers.remove(str(guild.id))
        server.delete()


@bot.event
async def on_message(message):
    if message.author.bot:
        return None

    server = Server(message.guild.id)

    if 'assists' in server.config and server.config['assists'] == 1 and server.assistschannel == message.channel.id:
        await message.delete()
        messages = []
        content = message.content

        parsed_url = urlparse(content)

        if parsed_url.hostname == 'www.torn.com' and parsed_url.path in ('/loader.php', '/loader2.php') and \
                parse_qs(parsed_url.query)["sid"][0] in ('attack', 'getInAttack'):
            embed = discord.Embed()
            embed.title = f'{message.author.nick if message.author.nick is not None else message.author.name} has ' \
                          f'requested an assist from {message.guild.name}:'
            embed.description = f'[{content}]({content})'
            embed.timestamp = datetime.datetime.utcnow()
            embed.set_footer(text=utils.torn_timestamp())

            for server in ServerModel.objects(assistchannel__ne=0):
                if 'assists' not in server.config or server.config['assists'] == 0 or server.assistschannel == 0:
                    continue

                try:
                    guild = bot.get_guild(server.sid)
                except discord.Forbidden:
                    continue
                channel = discord.utils.get(guild.channels, id=server.assistschannel)

                if channel is None:
                    continue

                message = await channel.send(embed=embed)
                messages.append(message)

            server = Server(message.guild.id)

            if len(server.admins) == 0:
                return None
            else:
                tid = parse_qs(urlparse(content).query)

                try:
                    user_data = tasks.tornget(f'user/{tid["user2ID"][0]}?selections=',
                                              key=User(random.choice(server.admins)).key)
                except Exception as e:
                    utils.get_logger().exception(e)
                    return None

                embed.add_field(name='Target', value=f'{user_data["name"]} [{user_data["player_id"]}]')
                embed.add_field(name='Level', value=user_data["level"])

                if user_data["faction"]["faction_id"] == 0:
                    faction = 'None'
                else:
                    faction = f'[{user_data["faction"]["faction_name"]}](https://www.torn.com/factions.php?step=' \
                              f'profile&ID={user_data["faction"]["faction_id"]})'

                embed.add_field(name='Faction', value=faction)
                embed.add_field(name='Life', value=f'{user_data["life"]["current"]}/{user_data["life"]["maximum"]}')

                for message in messages:
                    await message.edit(embed=embed)

            await asyncio.sleep(300)
            for message in messages:
                await message.delete()

            return None

    if len(server.admins) == 0:
        await bot.process_commands(message)

    for faction in server.factions:
        faction = utils.first(FactionModel.objects(tid=int(faction)))

        if faction is None:
            continue
        elif faction.vaultconfig['withdrawal'] == 0:
            continue

        if message.channel.id == faction.vaultconfig['withdrawal'] and message.clean_content[0] != server.prefix:
            await message.delete()
            embed = discord.Embed()
            embed.title = "Bot Channel"
            embed.description = "This channel is only for vault withdrawals. Please do not post any other messages in" \
                                " this channel."
            message = await message.channel.send(embed=embed)
            await asyncio.sleep(30)
            await message.delete()
            return None

    await bot.process_commands(message)


@bot.command()
async def ping(ctx):
    '''
    Shows the ping to the server
    '''

    latency = bot.latency
    botlogger.info(f'Latency: {latency}')

    embed = discord.Embed()
    embed.title = "Latency"
    embed.description = f'{latency} seconds'
    await ctx.send(embed=embed)


@bot.command()
async def help(ctx):
    embed = discord.Embed()
    embed.title = "Bot Help"
    embed.description = "Take a look at the [documentation](https://torn.deek.sh/bot/documentation) if you need any " \
                        "help."
    embed.add_field(name="General Information", value="[Tornium](https://torn.deek.sh/) | "
                                                      "[Tornium Bot](https://torn.deek.sh/bot)")
    embed.add_field(name="Support Server", value="[tiksan](https://discordapp.com/users/695828257949352028)")
    await ctx.send(embed=embed)


if __name__ == "__main__":
    redis = get_redis()
    bot.run(redis.get('tornium:settings:bottoken'))
