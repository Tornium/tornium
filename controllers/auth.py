# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>


from flask import Blueprint, request, redirect, render_template, abort, url_for
from flask_login import logout_user, login_user
from is_safe_url import is_safe_url

from models.user import User
from models.usermodel import UserModel
from redisdb import get_redis
import utils


mod = Blueprint('authroutes', __name__)


@mod.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    user: UserModel = utils.first(UserModel.objects(key=request.form['key']))

    if user is None or not user.pro:
        abort(403)

    user = User(user.tid)
    login_user(user)
    next = request.args.get('next')

    if next is None or next == 'None':
        return redirect(url_for('baseroutes.index'))

    if not get_redis().get('dev'):
        if not is_safe_url(next, {'torn.deek.sh'}):
            abort(400)
    return redirect(next or url_for('baseroutes.index'))


@mod.route('/logout', methods=['POST'])
def logout():
    logout_user()
    return redirect(url_for('baseroutes.index'))


