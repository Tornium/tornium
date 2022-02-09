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
import logging
import re

from flask import render_template

from utils.errors import *


def get_logger():
    return logging.getLogger("server")


def get_tid(name):
    try:
        return int(re.compile(r"\[(\d+)\]").findall(name)[0])
    except IndexError:
        try:
            return int(name)
        except ValueError:
            return 0


def get_torn_name(name):
    return re.sub("[[].*?[]]", "", name).replace(' ', '')


def handle_torn_error(error: str):
    error = remove_str(error)

    if error == 0:
        return render_template('/errors/error.html', title='Unknown Error',
                               error='The Torn API has returned an unknown error.')
    elif error == 1:
        return render_template('/errors/error.html', title='Empty Key',
                               error='The passed Torn API key was empty (i.e. no Torn API key was passed).')
    elif error == 2:
        return render_template('/errors/error.html', title='Incorrect Key',
                               error='The passed Torn API key was not a valid key.')
    elif error == 5:
        return render_template('/errors/error.html', title='Too Many Requests',
                               error='The passed Torn API key has had more than 100 requests sent to the Torn '
                                     'API server. Please try again in a couple minutes.')
    elif error == 8:
        return render_template('/errors/error.html', title='IP Block',
                               error='The server on which this site is hosted has made more than 2000 API calls '
                                     'this minute has has been temporarily banned by Torn\'s servers for a minute. '
                                     'Please contact the administrators of this site to inform them of this so '
                                     'that changes can be made.')
    elif error == 9:
        return render_template('/errors/error.html', title='API System Disabled',
                               error='Torn\'s API system has been temporarily disabled. Please try again in a '
                                     'couple minutes.')
    elif error == 10:
        return render_template('/errors/error.html', title='Key Owner Fedded',
                               error='The owner of the passed API key has been fedded. Please verify that the '
                                     'inputted API key is correct.')
    elif error == 11:
        return render_template('/errors/error.html', title='Key Change Error',
                               error='You can only change your API key once every 60 seconds.')
    elif error == 13:
        return render_template('/errors/error.html', title='Key Change Error',
                               error='The owner of the passed API key has not been online for more than 7 days. '
                                     'Please verify that the inputted API key is correct.')
    else:
        return render_template('/errors/error.html', title='Miscellaneous Error',
                               error=f'The Torn API has responded with error code {error}')


def handle_discord_error(error: str):
    error = remove_str(error)

    if error == 0:
        return render_template('/errors/error.html', title='General Error',
                               error=f'The Discord API has returned a general error.')
    elif error == 10003:
        return render_template('/errors/error.html', title='Unknown Channel',
                               error='The passed guild channel could not be found.')
    elif error == 10004:
        return render_template('/errors/error.html', title='Unknown Guild', 
                               error='The passed guild could not be found.')
    elif error == 10007:
        return render_template('/errors/error.html', title='Unknown Member', 
                               error='The passed guild member could not be found.')
    elif error == 10008:
        return render_template('/errors/error.html', title='Unknown Message', 
                               error='The passed message could not be found.')
    elif error == 10011:
        return render_template('/errors/error.html', title='Unknown Role',
                               error='The passed guild role could not be found.')
    elif error == 10012:
        return render_template('/errors/error.html', title='Unknown Token',
                               error='The passed bot token is not correct. Please immediately contact the bot/app '
                                     'hoster in order for the bot token to be replaced.')
    elif error == 10013:
        return render_template('/errors/error.html', title='Unknown User',
                               error='The passed Discord user could not be found.')
    elif error == 40001:
        return render_template('/errors/error.html', title='Unauthorized',
                               error='The passed bot token is not valid. Please immediately contact the bot/app '
                                     'hoster in order for the bot token to be replaced.')
    else:
        return render_template('/errors/error.html', title='Miscellaneous Error',
                               error=f'The Discord API has responded with error code {error} that is not currently in '
                                     f'the handled list of Discord API errors. Please report this error to the '
                                     f'developer(s). A full list of Discord API errors can be found at '
                                     f'https://discord.com/developers/docs/topics/opcodes-and-status-codes#json')


def now():
    return int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())


def remove_str(text):
    return int(''.join(filter(lambda x: x.isdigit(), text)))


def rel_time(time):
    delta = now() - int(time.timestamp())

    if delta < 60:  # One minute
        return 'Now'
    elif delta < 3600:  # Sixty minutes
        if int(round(delta/60)) == 1:
            return f'{int(round(delta/60))} minute ago'
        else:
            return f'{int(round(delta/60))} minutes ago'
    elif delta < 86400:  # One day
        if int(round(delta/3600)) == 1:
            return f'{int(round(delta/3600))} hours ago'
        else:
            return f'{int(round(delta/3600))} hours ago'
    elif delta < 2592000:  # Thirty days
        if int(round(delta/86400)) == 1:
            return f'{int(round(delta/86400))} day ago'
        else:
            return f'{int(round(delta/86400))} days ago'
    elif delta < 31104000:  # Twelve months
        if int(round(delta/2592000)) == 1:
            return f'{int(round(delta/2592000))} month ago'
        else:
            return f'{int(round(delta/2592000))} months ago'
    else:
        return 'A long time ago'


def torn_timestamp(timestamp=None):
    if timestamp is None:
        return datetime.datetime.utcnow().strftime('%m/%d %H:%M:%S TCT')
    else:
        return datetime.datetime.fromtimestamp(timestamp).strftime('%m/%d %H:%M:%S TCT')


def remove_html(text):
    cleaner = re.compile("<.*?>")
    return re.sub(cleaner, '', text)


def first(array):
    return None if len(array) == 0 else array[0]


def last(array):
    if len(array) == 0:
        return None
    elif len(array) == 1:
        return array[0]
    else:
        return array[len(array) - 1]
