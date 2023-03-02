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

from flask import flash, render_template, request
from flask_login import current_user, fresh_login_required

from tornium_celery.tasks.api import discordget
from tornium_commons.errors import DiscordError, NetworkingError
from tornium_commons.models import FactionModel, ServerModel

import utils
from controllers.faction.decorators import aa_required, fac_required
from models.faction import Faction
from models.server import Server


@fresh_login_required
@fac_required
@aa_required
def bot(*args, **kwargs):
    faction = Faction(current_user.factiontid)

    if faction.guild == 0:
        vault_config = {"banking": 0, "banker": 0}
        config = {"vault": 0, "stats": 1}
        flash("Remember to set the faction server before performing any other setup.")
    else:
        server = Server(faction.guild)

        if faction.tid not in server.factions:
            vault_config = {"banking": 0, "banker": 0}
            config = {"vault": 0, "stats": 1}
            flash("Remember to add the faction to the server's list of factions before performing any other setup")
        else:
            vault_config = faction.vault_config
            config = faction.config

    if request.method == "POST":
        faction_model = FactionModel.objects(tid=current_user.factiontid).first()

        if request.form.get("guildid") is not None:
            guild: ServerModel = ServerModel.objects(sid=request.form.get("guildid")).first()
            if guild is None:
                return render_template(
                    "errors/error.html",
                    title="Unknown Guild",
                    error=f"The Discord server with ID {request.form.get('guildid')} could not be found.",
                )

            faction.guild = request.form.get("guildid")
            faction_model.guild = request.form.get("guildid")
            faction_model.save()
        elif request.form.get("banking") is not None:
            guild: ServerModel = ServerModel.objects(sid=faction.guild).first()

            if guild is None:
                return render_template(
                    "errors/error.html",
                    title="Unknown Guild",
                    error=f"The Discord server with ID {faction.guild} could not be found.",
                )

            try:
                channel = discordget(f'channels/{request.form.get("banking")}')
            except DiscordError as e:
                return utils.handle_discord_error(e)
            except NetworkingError as e:
                return render_template(
                    "errors/error.html",
                    title="Discord Networking Error",
                    error=f"The Discord API has responded with HTTP error code {e.code}.",
                )
            except Exception as e:
                return render_template("errors/error.html", title="Error", error=str(e))

            faction_model.vaultconfig["banking"] = int(channel["id"])
            faction_model.save()
        elif request.form.get("banker") is not None:
            guild: ServerModel = ServerModel.objects(sid=faction.guild).first()

            if guild is None:
                return render_template(
                    "errors/error.html",
                    title="Unknown Guild",
                    error=f"The Discord server with ID {faction.guild} could not be found.",
                )

            try:
                roles = discordget(f"guilds/{faction.guild}/roles")
            except DiscordError as e:
                return utils.handle_discord_error(e)
            except NetworkingError as e:
                return render_template(
                    "errors/error.html",
                    title="Discord Networking Error",
                    error=f"The Discord API has responded with HTTP error code {e.code}.",
                )
            except Exception as e:
                return render_template("errors/error.html", title="Error", error=str(e))

            for role in roles:  # TODO: Add error message for role not found in server
                if role["id"] == request.form.get("banker"):
                    faction_model.vaultconfig["banker"] = int(request.form.get("banker"))
                    faction_model.save()
        elif (request.form.get("enabled") is not None) ^ (request.form.get("disabled") is not None):
            if request.form.get("enabled") is not None:
                faction_model.config["vault"] = 1
            else:
                faction_model.config["vault"] = 0

            faction_model.save()

    return render_template(
        "faction/bot.html",
        guildid=faction.guild,
        vault_config=vault_config,
        config=config,
    )
