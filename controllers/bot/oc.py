# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from flask import render_template
from flask_login import login_required


@login_required
def oc_dashboard(guildid):
    return render_template(
        "bot/oc.html",
        guildid=guildid,
    )
