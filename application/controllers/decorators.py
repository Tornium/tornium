# Copyright (C) 2021-2025 tiksan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import secrets
import time
from functools import partial, wraps

from flask import abort, redirect, render_template, request, url_for
from flask_login import current_user, login_fresh
from tornium_commons import Config, rds


def token_required(f=None, setnx=False):
    if not f:
        return partial(token_required, setnx=setnx)

    @wraps(f)
    def wrapper(*args, **kwargs):
        if not login_fresh():
            return redirect(url_for("authroutes.login"))

        if request.args.get("token") is None and setnx:
            redis_client = rds()
            client_token = secrets.token_urlsafe()

            if redis_client.exists(f"tornium:token:{client_token}"):
                return render_template(
                    "errors/error.html",
                    title="Security Error",
                    error="The generated client token already exists. Please try again.",
                )

            redis_client.set(
                f"tornium:token:{client_token}",
                f"{int(time.time())}|{current_user.tid}",
                nx=True,
                ex=300,
            )

            return redirect(url_for(request.url_rule.endpoint, token=client_token))
        elif request.args.get("token") is None and not setnx:
            return abort(401)

        redis_client = rds()
        client_token = request.args.get("token")
        client_token_redis = redis_client.get(f"tornium:token:{client_token}")

        if client_token_redis is None:
            return redirect(url_for(request.url_rule.endpoint))
        elif int(client_token_redis.split("|")[1]) != int(current_user.tid):
            redis_client.delete(f"tornium:token:{client_token}")

            return redirect(url_for(request.url_rule.endpoint))

        kwargs["token"] = client_token

        return f(*args, **kwargs)

    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not login_fresh():
            return redirect(url_for("authroutes.login")), 401
        elif current_user.tid not in Config.from_json().admin_users:
            return render_template("errors/admin_denied.html"), 403

        return f(*args, **kwargs)

    return wrapper
