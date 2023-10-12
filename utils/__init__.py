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

from urllib.parse import urlparse

import peewee
from flask import render_template

import utils.tornium_ext


def handle_torn_error(error):
    if error.code == 0:
        return render_template(
            "/errors/error.html",
            title="Unknown Error",
            error="The Torn API has returned an unknown error.",
        )
    elif error.code == 1:
        return render_template(
            "/errors/error.html",
            title="Empty Key",
            error="The passed Torn API key was empty (i.e. no Torn API key was passed).",
        )
    elif error.code == 2:
        return render_template(
            "/errors/error.html",
            title="Incorrect Key",
            error="The passed Torn API key was not a valid key.",
        )
    elif error.code == 5:
        return render_template(
            "/errors/error.html",
            title="Too Many Requests",
            error="The passed Torn API key has had more than 100 requests sent to the Torn "
            "API server. Please try again in a couple minutes.",
        )
    elif error.code == 8:
        return render_template(
            "/errors/error.html",
            title="IP Block",
            error="The server on which this site is hosted has made more than 2000 API calls "
            "this minute has has been temporarily banned by Torn's servers for a minute. "
            "Please contact the administrators of this site to inform them of this so "
            "that changes can be made.",
        )
    elif error.code == 9:
        return render_template(
            "/errors/error.html",
            title="API System Disabled",
            error="Torn's API system has been temporarily disabled. Please try again in a " "couple minutes.",
        )
    elif error.code == 10:
        return render_template(
            "/errors/error.html",
            title="Key Owner Fedded",
            error="The owner of the passed API key has been fedded. Please verify that the "
            "inputted API key is correct.",
        )
    elif error.code == 11:
        return render_template(
            "/errors/error.html",
            title="Key Change Error",
            error="You can only change your API key once every 60 seconds.",
        )
    elif error.code == 13:
        return render_template(
            "/errors/error.html",
            title="Key Change Error",
            error="The owner of the passed API key has not been online for more than 7 days. "
            "Please verify that the inputted API key is correct.",
        )
    elif error.code == 17:
        return render_template(
            "/errors/error.html",
            title="Internal Torn API Error",
            error="An internal backend error has occurred with the Torn API. Please try again.",
        )
    else:
        return render_template(
            "/errors/error.html",
            title="Miscellaneous Error",
            error=f"The Torn API has responded with error code {error.code}",
        )


def handle_discord_error(error):
    if error.code == 0:
        return render_template(
            "/errors/error.html",
            title="General Error",
            error="The Discord API has returned a general error.",
        )
    elif error.code == 10003:
        return render_template(
            "/errors/error.html",
            title="Unknown Channel",
            error="The passed guild channel could not be found.",
        )
    elif error.code == 10004:
        return render_template(
            "/errors/error.html",
            title="Unknown Guild",
            error="The passed guild could not be found.",
        )
    elif error.code == 10007:
        return render_template(
            "/errors/error.html",
            title="Unknown Member",
            error="The passed guild member could not be found.",
        )
    elif error.code == 10008:
        return render_template(
            "/errors/error.html",
            title="Unknown Message",
            error="The passed message could not be found.",
        )
    elif error.code == 10011:
        return render_template(
            "/errors/error.html",
            title="Unknown Role",
            error="The passed guild role could not be found.",
        )
    elif error.code == 10012:
        return render_template(
            "/errors/error.html",
            title="Unknown Token",
            error="The passed bot token is not correct. Please immediately contact the bot/app "
            "hoster in order for the bot token to be replaced.",
        )
    elif error.code == 10013:
        return render_template(
            "/errors/error.html",
            title="Unknown User",
            error="The passed Discord user could not be found.",
        )
    elif error.code == 40001:
        return render_template(
            "/errors/error.html",
            title="Unauthorized",
            error="The passed bot token is not valid. Please immediately contact the bot/app "
            "hoster in order for the bot token to be replaced.",
        )
    else:
        return render_template(
            "/errors/error.html",
            title="Miscellaneous Error",
            error=f"The Discord API has responded with error code {error.code} that is not currently in "
            f"the handled list of Discord API errors. Please report this error.code to the "
            f"developer(s). A full list of Discord API errors can be found at "
            f"https://discord.com/developers/docs/topics/opcodes-and-status-codes#json",
        )


def handle_networking_error(error):
    if error.code == 408 and urlparse(error.url).hostname == "www.torn.com":
        return render_template(
            "/errors/error.html",
            title="Torn API Timed Out",
            error="The Torn API did not respond within the prescribed time period. Please try again. This issue "
            "originates from Torn's servers.",
        )

    return render_template(
        "/errors/error.html",
        title="Miscellaneous Error",
        error=f"An API has responded with HTTP {error.code}.",
    )


def table_order(ordering_direction: str, field: peewee.Field):
    if ordering_direction == "asc":
        return field.asc()
    else:
        return field.desc()
