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

import sys

from discord.ext import commands, tasks
import requests

sys.path.append('..')

from redisdb import get_redis


class Periodic(commands.Cog):
    def __init__(self, bot, logger):
        self.bot = bot
        self.logger = logger
        self.honeybadger.start()
        
    def cog_unload(self):
        self.honeybadger.cancel()
        
    @tasks.loop(minutes=1)
    async def honeybadger(self):
        redis = get_redis()

        if redis.get('tornium:settings:honeybotcheckin') is None or redis.get('tornium:settings:honeybotcheckin') == '':
            return

        request = requests.get(redis.get('tornium:settings:honeybotcheckin'))
        self.logger.debug(f'Check-in made... HoneyBadger has responded with {request.content}.')
