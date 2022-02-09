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

import datetime
from decimal import Decimal
import re
import sys

import discord
import requests

sys.path.append('..')


def get_prefix(bot, message):
    from models.server import Server
    return Server(message.guild.id).prefix


def text_to_num(text):
    text = text.upper().replace(",", "")
    numbers = re.sub(f'[a-z]', '', text.lower())

    if "K" in text:
        return int(Decimal(numbers) * 1000)
    elif "M" in text:
        return int(Decimal(numbers) * 1000000)
    elif "B" in text:
        return int(Decimal(numbers) * 1000000000)
    else:
        return int(Decimal(numbers))


def num_to_text(num):
    num = float('{:.3g}'.format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])


def commas(number):
    return "{:,}".format(number)


async def tornget(ctx, logger, endpoint, key):
    request = requests.get(f'https://api.torn.com/{endpoint}&key={key}&comment=Tornium')

    if request.status_code != 200:
        embed = discord.Embed()
        embed.title = "Error"
        embed.description = f'Something has possibly gone wrong with the request to the Torn API with ' \
                            f'HTTP status code {request.status_code} has been given at ' \
                            f'{datetime.datetime.now()}.'
        await ctx.send(embed=embed)
        logger.error(f'The Torn API has responded with HTTP status code {request.status_code}.')
        return Exception

    if 'error' in request.json():
        error = request.json()['error']
        embed = discord.Embed()
        embed.title = "Error"
        embed.description = f'Something has gone wrong with the request to the Torn API with error code ' \
                            f'{error["code"]} ({error["error"]}). Visit the [Torn API documentation]' \
                            f'(https://api.torn.com/) to see why the error was raised.'
        await ctx.send(embed=embed)
        logger.error(f'The Torn API has responded with error code {error["code"]}.')
        raise Exception

    return request.json()
