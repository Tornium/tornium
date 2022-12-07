# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from flask import render_template, request, abort
from flask_login import current_user, login_required

from controllers.faction.decorators import fac_required
from models.faction import Faction
from models.factionmodel import FactionModel
from models.servermodel import ServerModel
import tasks
import utils


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
                channel = tasks.discordget(f'channels/{request.form.get("odchannel")}')
            except utils.DiscordError as e:
                return utils.handle_discord_error(e)
            except utils.NetworkingError as e:
                return render_template(
                    "errors/error.html",
                    title="Discord Networking Error",
                    error=f"The Discord API has responded with HTTP error code "
                    f"{e.code}.",
                )
            except Exception as e:
                raise e

            config = faction_model.chainconfig
            config["odchannel"] = int(channel["id"])
            faction_model.save()
        elif (request.form.get("odenabled") is not None) ^ (
            request.form.get("oddisabled") is not None
        ):
            config = faction_model.chainconfig

            if request.form.get("odenabled") is not None:
                config["od"] = 1
                faction_model.save()
            if request.form.get("oddisabled") is not None:
                config["od"] = 0
                faction_model.save()

    return render_template("faction/chain.html", faction=faction)
