# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from flask import Blueprint

mod = Blueprint('statroutes', __name__)


@mod.route('/statdb')
def index():
    return ''
