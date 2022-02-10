# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

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
