# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from flask import render_template
from flask_login import login_required

from models.faction import Faction
from models.server import Server


@login_required
def verify_dashboard(guildid):
    guild = Server(guildid)

    return render_template(
        "bot/verify.html",
        channels=guild.get_text_channels(),
        guild=guild,
    )


@login_required
def verify_faction_modal(guildid, factiontid):
    guild = Server(guildid)
    faction = Faction(factiontid)

    return render_template("bot/verifymodal.html", faction=faction)
