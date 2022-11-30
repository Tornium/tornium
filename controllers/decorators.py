# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from functools import wraps

from flask import abort, render_template
from flask_login import current_user


def pro_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.pro:
            return render_template("errors/402.html"), 402

        return func(*args, **kwargs)

    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.admin:
            return abort(403)
        else:
            return f(*args, **kwargs)

    return wrapper
