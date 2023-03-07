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

from flask import abort, render_template, request
from flask_login import current_user, login_required

from tornium_celery.tasks.api import discordget
from tornium_commons.errors import DiscordError, NetworkingError
from tornium_commons.models import FactionModel, ServerModel

import utils
from controllers.faction.decorators import fac_required
from models.faction import Faction


@login_required
@fac_required
def chain(*args, **kwargs):
    faction = Faction(current_user.factiontid)

    if request.method == "POST":
        if not current_user.aa:
            abort(403)

        faction_model = FactionModel.objects(tid=current_user.factiontid).first()

        if request.form.get("odchannel") is not None:
            guild: ServerModel = ServerModel.objects(sid=faction.guild).first()

            if guild is None:
                return render_template(
                    "errors/error.html",
                    title="Unknown Guild",
                    error=f"The Discord server with ID {faction.guild} could not be found.",
                )

            try:
                channel = discordget(f'channels/{request.form.get("odchannel")}')
            except DiscordError as e:
                return utils.handle_discord_error(e)
            except NetworkingError as e:
                return render_template(
                    "errors/error.html",
                    title="Discord Networking Error",
                    error=f"The Discord API has responded with HTTP error code {e.code}.",
                )
            except Exception as e:
                raise e

            config = faction_model.chainconfig
            config["odchannel"] = int(channel["id"])
            faction_model.save()
        elif (request.form.get("odenabled") is not None) ^ (request.form.get("oddisabled") is not None):
            config = faction_model.chainconfig

            if request.form.get("odenabled") is not None:
                config["od"] = 1
                faction_model.save()
            if request.form.get("oddisabled") is not None:
                config["od"] = 0
                faction_model.save()

    return render_template("faction/chain.html", faction=faction)
