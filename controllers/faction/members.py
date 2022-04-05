#  Copyright (C) tiksan - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by tiksan <webmaster@deek.sh>

from flask import render_template, request
from flask_login import login_required

from controllers.faction.decorators import *
from models.usermodel import UserModel


@login_required
@fac_required
def members(*args, **kwargs):
    fac_members = UserModel.objects(factionid=kwargs['faction'].tid)
    return render_template('faction/members.html', members=fac_members)
