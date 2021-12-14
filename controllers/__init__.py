# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster.deeksh@gmail.com>

from flask import Blueprint, render_template, redirect, send_from_directory, request

mod = Blueprint('baseroutes', __name__)


@mod.route('/')
@mod.route('/index')
def index():
    return render_template('index.html')


@mod.route('/pricing')
def pricing():
    return redirect('https://torn.deek.sh/pricing')


@mod.route('/robots.txt')
def static():
    return send_from_directory('static', request.path[1:])
