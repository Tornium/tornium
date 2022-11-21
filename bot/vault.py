# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import asyncio
import random
import sys
import time
from urllib import request

import discord
from discord.ext import commands

sys.path.append("..")

from bot import botutils
from models.faction import Faction
from models.server import Server
from models.user import User
from models.usermodel import UserModel
from models.withdrawalmodel import WithdrawalModel
from redisdb import get_redis
import utils


class Vault(commands.Cog):
    def __init__(self, bot, logger):
        self.bot = bot
        self.logger = logger

    @commands.command(aliases=["req", "with", "w", "W", "Withdraw"])
    async def withdraw(self, ctx, arg):
        await ctx.message.delete()

        server = Server(ctx.message.guild.id)
        user = UserModel.objects(discord_id=ctx.message.author.id).first()

        if user is None:
            if len(server.admins) == 0:
                embed = discord.Embed()
                embed.title = "No Admins"
                embed.description = "There are no admins currently signed into Tornium."
                await ctx.send(embed=embed)
                return None

            admin = UserModel.objects(tid=random.choice(server.admins)).first()

            if admin is None:
                embed = discord.Embed()
                embed.title = "Admin Not Found"
                embed.description = "Admin not found in the database. Please try again."
                await ctx.send(embed=embed)
                return None
            elif admin.key == "":
                embed = discord.Embed()
                embed.title = " Admin Key Not Found"
                embed.description = "Admin located in the database, but no key was found. Please try again."
                await ctx.send(embed=embed)
                return None

            user_data = await botutils.tornget(
                ctx,
                self.logger,
                f"user/{ctx.message.author.id}?selections=profile,discord",
                admin.key,
            )

            user = UserModel(
                tid=user_data["player_id"],
                name=user_data["name"],
                level=user_data["level"],
                last_refresh=utils.now(),
                discord_id=user_data["discord"]["discordID"]
                if user_data["discord"]["discordID"] != ""
                else 0,
                factionid=user_data["faction"]["faction_id"],
                status=user_data["last_action"]["status"],
                last_action=user_data["last_action"]["timestamp"],
            )
            user.save()

            if user.discord_id == 0:
                embed = discord.Embed()
                embed.title = "Requires Verification"
                embed.description = (
                    "You are required to be verified officially through the "
                    "[official Torn Discord server](https://www.torn.com/discord) before being able to "
                    "utilize the banking features of this bot. If you have recently verified, please "
                    "wait for a minute or two before trying again."
                )
                await ctx.send(embed=embed)
                return None
        elif user.tid == 0:
            embed = discord.Embed()
            embed.title = "Requires Verification"
            embed.description = (
                "You are required to be verified officially through the "
                "[official Torn Discord server](https://www.torn.com/discord) before being able to "
                "utilize the banking features of this bot. If you have recently verified, please "
                "wait for a minute or two before trying again."
            )
            await ctx.send(embed=embed)
            return None

        client = get_redis()

        if client.get(f"tornium:banking-ratelimit:{user.tid}") is not None:
            embed = discord.Embed()
            embed.title = "Ratelimit Reached"
            embed.description = (
                f"You have reached the ratelimit on banking requests (once every minute). Please try "
                f'again in {client.ttl(f"tornium:banking-ratelimit:{user.tid}")} seconds.'
            )
            await ctx.send(embed=embed)
            return None
        else:
            client.set(f"tornium:banking-ratelimit:{user.tid}", 1)
            client.expire(f"tornium:banking-ratelimit:{user.tid}", 60)

        if arg.lower() == "all":
            cash = "all"
        else:
            cash = botutils.text_to_num(arg)

        if user.factionid == 0:
            embed = discord.Embed()
            embed.title = "Faction ID Error"
            embed.description = (
                f"The faction ID of {ctx.message.author.name} is not set regardless of the "
                f"forced refresh."
            )
            await ctx.send(embed=embed)
            return None

        faction = Faction(user.factionid)

        if user.factionid not in server.factions:
            embed = discord.Embed()
            embed.title = "Server Configuration Required"
            embed.description = (
                f"{ctx.guild.name} needs to be added to {faction.name}'s bot configuration and to "
                f"the server. Please contact the server administrators to do this via "
                f"[the dashboard](https://tornium.com/)."
            )
            await ctx.send(embed=embed)
            return None

        vault_config = faction.vault_config
        config = faction.config

        if (
            vault_config.get("banking") in [0, None]
            or vault_config.get("banker") in [0, None]
            or config.get("vault") in [0, None]
        ):
            embed = discord.Embed()
            embed.title = "Server Configuration Required"
            embed.description = (
                f"{ctx.guild.name} needs to be added to {faction.name}'s bot configuration and to "
                f"the server. Please contact the server administrators to do this via "
                f"[the dashboard](https://tornium.com/)."
            )
            await ctx.send(embed=embed)
            return None

        vault_balances = await botutils.tornget(
            ctx, self.logger, f"faction/?selections=donations", faction.rand_key()
        )

        if str(user.tid) in vault_balances["donations"]:
            if (
                cash != "all"
                and cash > vault_balances["donations"][str(user.tid)]["money_balance"]
            ):
                embed = discord.Embed()
                embed.title = "Not Enough Money"
                embed.description = (
                    f"You have requested {arg}, but only have "
                    f'{botutils.commas(vault_balances["donations"][str(user.tid)]["money_balance"])} '
                    f"in the vault."
                )
                message = await ctx.send(embed=embed)
                await asyncio.sleep(30)
                await message.delete()
                return None
            elif (
                cash == "all"
                and vault_balances["donations"][str(user.tid)]["money_balance"] <= 0
            ):
                embed = discord.Embed()
                embed.title = "Not Enough Money"
                embed.description = (
                    f"You have requested all of you money, but have no cash in the vault or "
                    f"a negative vault balance."
                )
                message = await ctx.send(embed=embed)
                await asyncio.sleep(30)
                await message.delete()
                return None

            channel = discord.utils.get(ctx.guild.channels, id=vault_config["banking"])
            request_id = WithdrawalModel.objects().count()

            embed = discord.Embed()
            embed.title = f"Vault Request #{request_id}"
            embed.description = (
                "Your request has been forwarded to the faction leadership."
            )
            original = await ctx.send(embed=embed)

            embed = discord.Embed()
            embed.title = f"Vault Request #{request_id}"
            send_link = f"https://tornium.com/faction/banking/fulfill/{request_id}"

            if cash != "all":
                embed.description = (
                    f"{user.name if user.name != '' else ctx.message.author.nick} is requesting {arg} "
                    f"from the faction vault. To fulfill this request, "
                    f"enter `?f {request_id}` in this channel."
                )
                embed.add_field(
                    name="Fulfill Link", value=f"[Fulfill Here]({send_link})"
                )
            else:
                embed.description = (
                    f"{user.name if user.name != '' else ctx.message.author.nick} is requesting "
                    f'{utils.commas(vault_balances["donations"][str(user.tid)]["money_balance"])} '
                    f"from the faction vault. To fulfill this request, "
                    f"enter `?f {request_id}` in this channel."
                )
                embed.add_field(
                    name="Fulfill Link", value=f"[Fulfill Here]({send_link})"
                )
            message = await channel.send(f'<@&{vault_config["banker"]}>', embed=embed)

            withdrawal = WithdrawalModel(
                wid=request_id,
                amount=cash
                if cash != "all"
                else vault_balances["donations"][str(user.tid)]["money_balance"],
                requester=user.tid,
                factiontid=user.factionid,
                time_requested=utils.now(),
                fulfiller=0,
                time_fulfilled=0,
                withdrawal_message=message.id,
                wtype=0,
            )
            withdrawal.save()
            await asyncio.sleep(30)
            await original.delete()
        else:
            embed = discord.Embed()
            embed.title = "Money Request Failed"
            embed.description = (
                "You are not a member of any stored factions. This requires your faction leadership "
                "to set up banking."
            )
            message = await ctx.send(embed=embed)
            await asyncio.sleep(30)
            await message.delete()

    @commands.command(aliases=["f"])
    async def fulfill(self, ctx, request):
        await ctx.message.delete()

        server = Server(ctx.message.guild.id)
        user = UserModel.objects(discord_id=ctx.message.author.id).first()

        if user is None:
            if len(server.admins) == 0:
                embed = discord.Embed()
                embed.title = "No Admins"
                embed.description = "There are no admins currently signed into Tornium."
                await ctx.send(embed=embed)
                return None

            admin = UserModel.objects(tid=random.choice(server.admins)).first()

            if admin is None:
                embed = discord.Embed()
                embed.title = "Admin Not Found"
                embed.description = "Admin not found in the database. Please try again."
                await ctx.send(embed=embed)
                return None
            elif admin.key == "":
                embed = discord.Embed()
                embed.title = " Admin Key Not Found"
                embed.description = "Admin located in the database, but no key was found. Please try again."
                await ctx.send(embed=embed)
                return None

            user_data = await botutils.tornget(
                ctx, self.logger, f"user/{ctx.message.author.id}?selections=", admin.key
            )

            user = UserModel(
                tid=user_data["player_id"],
                name=user_data["name"],
                level=user_data["level"],
                last_refresh=utils.now(),
                discord_id=user_data["discord"]["discordID"]
                if user_data["discord"]["discordID"] != ""
                else 0,
                factionid=user_data["faction"]["faction_id"],
                status=user_data["last_action"]["status"],
                last_action=user_data["last_action"]["timestamp"],
            )
            user.save()

            if user.discord_id == 0:
                embed = discord.Embed()
                embed.title = "Requires Verification"
                embed.description = (
                    "You are required to be verified officially through the "
                    "[official Torn Discord server](https://www.torn.com/discord) before being able to "
                    "utilize the banking features of this bot. If you have recently verified, please "
                    "wait for a minute or two before trying again."
                )
                await ctx.send(embed=embed)
                return None
        elif user.tid == 0:
            embed = discord.Embed()
            embed.title = "Requires Verification"
            embed.description = (
                "You are required to be verified officially through the "
                "[official Torn Discord server](https://www.torn.com/discord) before being able to "
                "utilize the banking features of this bot. If you have recently verified, please "
                "wait for a minute or two before trying again."
            )
            await ctx.send(embed=embed)
            return None

        user = User(user.tid)
        user.refresh(key=User(random.choice(server.admins)).key)

        if user.factiontid == 0:
            user.refresh(key=User(random.choice(server.admins)).key, force=True)

            if user.factiontid == 0:
                embed = discord.Embed()
                embed.title = "Faction ID Error"
                embed.description = (
                    f"The faction ID of {ctx.message.author.name} is not set regardless of the "
                    f"forced refresh."
                )
                await ctx.send(embed=embed)
                return None

        faction = Faction(user.factiontid)

        if user.factiontid not in server.factions:
            embed = discord.Embed()
            embed.title = "Server Configuration Required"
            embed.description = (
                f"{ctx.guild.name} needs to be added to {faction.name}'s bot configuration and to "
                f"the server. Please contact the server administrators to do this via "
                f"[the dashboard](https://tornium.com/)."
            )
            await ctx.send(embed=embed)
            return None

        vault_config = faction.vault_config
        config = faction.config

        if (
            vault_config.get("banking") in [0, None]
            or vault_config.get("banker") in [0, None]
            or config.get("vault") in [0, None]
        ):
            embed = discord.Embed()
            embed.title = "Server Configuration Required"
            embed.description = (
                f"{ctx.guild.name} needs to be added to {faction.name}'s bot configuration and to "
                f"the server. Please contact the server administrators to do this via "
                f"[the dashboard](https://tornium.com/)."
            )
            await ctx.send(embed=embed)
            return None

        banking_channel = discord.utils.get(
            ctx.guild.channels, id=vault_config["banking"]
        )
        withdrawal = WithdrawalModel.objects(wid=int(request)).first()

        if withdrawal is None:
            embed = discord.Embed()
            embed.title = "Request Does not Exist"
            embed.description = (
                f"Vault Request #{request} does not currently exist. Please verify that you entered "
                f"the correct vault request ID."
            )
            await ctx.send(embed=embed)
            return None

        # Message posted in banking channel
        withdrawal_message = await banking_channel.fetch_message(
            withdrawal.withdrawal_message
        )

        if withdrawal["fulfiller"] != 0:
            embed = discord.Embed()
            embed.title = "Request Already Fulfilled"
            embed.description = (
                f"Vault request #{request} has already been fulfilled by "
                f"{User(withdrawal.fulfiller).name} at "
                f"{utils.torn_timestamp(withdrawal.time_fulfilled)}."
            )
            await ctx.send(embed=embed)
            return None

        embed = discord.Embed()
        embed.title = withdrawal_message.embeds[0].title
        embed.add_field(
            name="Original Message", value=withdrawal_message.embeds[0].description
        )
        embed.description = f"This request has been fulfilled by {ctx.message.author.name} at {utils.torn_timestamp(utils.now())}."
        embed.timestamp = withdrawal_message.embeds[0].timestamp
        await withdrawal_message.edit(embed=embed)

        withdrawal.fulfiller = user.tid
        withdrawal.time_fulfilled = utils.now()
        withdrawal.save()

    @commands.command(pass_context=True, aliases=["balance", "bal"])
    async def fullbalance(self, ctx):
        await ctx.message.delete()

        server = Server(ctx.message.guild.id)
        user = UserModel.objects(discord_id=ctx.message.author.id).first()

        if user is None:
            if len(server.admins) == 0:
                embed = discord.Embed()
                embed.title = "No Admins"
                embed.description = "There are no admins currently signed into Tornium."
                await ctx.send(embed=embed)
                return None

            admin = UserModel.objects(tid=random.choice(server.admins)).first()

            if admin is None:
                embed = discord.Embed()
                embed.title = "Admin Not Found"
                embed.description = "Admin not found in the database. Please try again."
                await ctx.send(embed=embed)
                return None
            elif admin.key == "":
                embed = discord.Embed()
                embed.title = " Admin Key Not Found"
                embed.description = "Admin located in the database, but no key was found. Please try again."
                await ctx.send(embed=embed)
                return None

            user_data = await botutils.tornget(
                ctx, self.logger, f"user/{ctx.message.author.id}?selections=", admin.key
            )

            user = UserModel(
                tid=user_data["player_id"],
                name=user_data["name"],
                level=user_data["level"],
                last_refresh=utils.now(),
                discord_id=user_data["discord"]["discordID"]
                if user_data["discord"]["discordID"] != ""
                else 0,
                factionid=user_data["faction"]["faction_id"],
                status=user_data["last_action"]["status"],
                last_action=user_data["last_action"]["timestamp"],
            )
            user.save()

            if user.discord_id == 0:
                embed = discord.Embed()
                embed.title = "Requires Verification"
                embed.description = (
                    "You are required to be verified officially through the "
                    "[official Torn Discord server](https://www.torn.com/discord) before being able to "
                    "utilize the banking features of this bot. If you have recently verified, please "
                    "wait for a minute or two before trying again."
                )
                await ctx.send(embed=embed)
                return None
        elif user.tid == 0:
            embed = discord.Embed()
            embed.title = "Requires Verification"
            embed.description = (
                "You are required to be verified officially through the "
                "[official Torn Discord server](https://www.torn.com/discord) before being able to "
                "utilize the banking features of this bot. If you have recently verified, please "
                "wait for a minute or two before trying again."
            )
            await ctx.send(embed=embed)
            return None

        user = User(user.tid)
        user.refresh(key=User(random.choice(server.admins)).key)

        if user.factiontid == 0:
            user.refresh(key=User(random.choice(server.admins)).key, force=True)

            if user.factiontid == 0:
                embed = discord.Embed()
                embed.title = "Faction ID Error"
                embed.description = (
                    f"The faction ID of {ctx.message.author.name} is not set regardless of the "
                    f"forced refresh."
                )
                await ctx.send(embed=embed)
                return None

        faction = Faction(user.factiontid)

        if user.factiontid not in server.factions:
            embed = discord.Embed()
            embed.title = "Server Configuration Required"
            embed.description = (
                f"{ctx.guild.name} needs to be added to {faction.name}'s bot configuration and to "
                f"the server. Please contact the server administrators to do this via "
                f"[the dashboard](https://tornium.com/)."
            )
            await ctx.send(embed=embed)
            return None

        config = faction.config

        if config.get("vault") in [0, None]:
            embed = discord.Embed()
            embed.title = "Server Configuration Required"
            embed.description = (
                f"{ctx.guild.name} needs to be added to {faction.name}'s bot configuration and to "
                f"the server. Please contact the server administrators to do this via "
                f"[the dashboard](https://tornium.com/)."
            )
            await ctx.send(embed=embed)
            return None

        faction_balances = (
            await botutils.tornget(
                ctx, self.logger, "faction/?selections=donations", faction.rand_key()
            )
        )["donations"]

        if str(user.tid) not in faction_balances:
            embed = discord.Embed()
            embed.title = "Error"
            embed.description = (
                f"{user.name} is not in {faction.name}'s donations list according to the Torn API. "
                f"If you think that this is an error, please report this to the developers of this bot."
            )
            await ctx.send(embed=embed)
            return None

        embed = discord.Embed()
        embed.title = f'Value Balance of {user.name if user.name != "" else ctx.message.author.name}'
        embed.description = (
            f'{user.name if user.name != "" else ctx.message.author.name} has '
            f'{botutils.commas(faction_balances[str(user.tid)]["money_balance"])} in '
            f"{faction.name}'s vault."
        )
        message = await ctx.send(embed=embed)
        await asyncio.sleep(30)
        await message.delete()

    @commands.command(pass_context=True, aliases=["b"])
    async def simplebalance(self, ctx):
        await ctx.message.delete()

        server = Server(ctx.message.guild.id)
        user = UserModel.objects(discord_id=ctx.message.author.id).first()

        if user is None:
            if len(server.admins) == 0:
                embed = discord.Embed()
                embed.title = "No Admins"
                embed.description = "There are no admins currently signed into Tornium."
                await ctx.send(embed=embed)
                return None

            admin = UserModel.objects(tid=random.choice(server.admins)).first()

            if admin is None:
                embed = discord.Embed()
                embed.title = "Admin Not Found"
                embed.description = "Admin not found in the database. Please try again."
                await ctx.send(embed=embed)
                return None
            elif admin.key == "":
                embed = discord.Embed()
                embed.title = " Admin Key Not Found"
                embed.description = "Admin located in the database, but no key was found. Please try again."
                await ctx.send(embed=embed)
                return None

            user_data = await botutils.tornget(
                ctx, self.logger, f"user/{ctx.message.author.id}?selections=", admin.key
            )

            user = UserModel(
                tid=user_data["player_id"],
                name=user_data["name"],
                level=user_data["level"],
                last_refresh=utils.now(),
                discord_id=user_data["discord"]["discordID"]
                if user_data["discord"]["discordID"] != ""
                else 0,
                factionid=user_data["faction"]["faction_id"],
                status=user_data["last_action"]["status"],
                last_action=user_data["last_action"]["timestamp"],
            )
            user.save()

            if user.discord_id == 0:
                embed = discord.Embed()
                embed.title = "Requires Verification"
                embed.description = (
                    "You are required to be verified officially through the "
                    "[official Torn Discord server](https://www.torn.com/discord) before being able to "
                    "utilize the banking features of this bot. If you have recently verified, please "
                    "wait for a minute or two before trying again."
                )
                await ctx.send(embed=embed)
                return None
        elif user.tid == 0:
            embed = discord.Embed()
            embed.title = "Requires Verification"
            embed.description = (
                "You are required to be verified officially through the "
                "[official Torn Discord server](https://www.torn.com/discord) before being able to "
                "utilize the banking features of this bot. If you have recently verified, please "
                "wait for a minute or two before trying again."
            )
            await ctx.send(embed=embed)
            return None

        user = User(user.tid)
        user.refresh(key=User(random.choice(server.admins)).key)

        if user.factiontid == 0:
            user.refresh(key=User(random.choice(server.admins)).key, force=True)

            if user.factiontid == 0:
                embed = discord.Embed()
                embed.title = "Faction ID Error"
                embed.description = (
                    f"The faction ID of {ctx.message.author.name} is not set regardless of the "
                    f"forced refresh."
                )
                await ctx.send(embed=embed)
                return None

        faction = Faction(user.factiontid)

        if user.factiontid not in server.factions:
            embed = discord.Embed()
            embed.title = "Server Configuration Required"
            embed.description = (
                f"{ctx.guild.name} needs to be added to {faction.name}'s bot configuration and to "
                f"the server. Please contact the server administrators to do this via "
                f"[the dashboard](https://tornium.com/)."
            )
            await ctx.send(embed=embed)
            return None

        config = faction.config

        if config.get("vault") in [0, None]:
            embed = discord.Embed()
            embed.title = "Server Configuration Required"
            embed.description = (
                f"{ctx.guild.name} needs to be added to {faction.name}'s bot configuration and to "
                f"the server. Please contact the server administrators to do this via "
                f"[the dashboard](https://tornium.com/)."
            )
            await ctx.send(embed=embed)
            return None

        faction_balances = (
            await botutils.tornget(
                ctx, self.logger, "faction/?selections=donations", faction.rand_key()
            )
        )["donations"]

        if str(user.tid) not in faction_balances:
            embed = discord.Embed()
            embed.title = "Error"
            embed.description = (
                f"{user.name} is not in {faction.name}'s donations list according to the Torn API. "
                f"If you think that this is an error, please report this to the developers of this bot."
            )
            await ctx.send(embed=embed)
            return None

        embed = discord.Embed()
        embed.title = f'Value Balance of {user.name if user.name != "" else ctx.message.author.name}'

        embed.description = (
            f'{user.name if user.name != "" else ctx.message.author.name} has '
            f'{botutils.num_to_text(faction_balances[str(user.tid)]["money_balance"])} in '
            f"{faction.name}'s vault."
        )
        message = await ctx.send(embed=embed)
        await asyncio.sleep(30)
        await message.delete()
