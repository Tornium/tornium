# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>


from flask import Blueprint, render_template, request, jsonify


mod = Blueprint('errors', __name__)


@mod.app_errorhandler(400)
def error400(e):
    """
    Returns the 400 error page

    :param e: HTTP error
    """

    return render_template('/errors/400.html'), 400


@mod.app_errorhandler(403)
def error403(e):
    """
    Returns the 403 error page.

    :param e: HTTP error
    """

    return render_template('/errors/403.html'), 403


@mod.app_errorhandler(404)
def error404(e):
    """
    Returns the 404 error page.

    :param e: HTTP error
    """

    if not request.path.startswith('/api') or request.path in ['/api', '/api/documentation']:
        return render_template('/errors/404.html'), 404
    else:
        return jsonify({
            'code': 4010,  # TODO: Update code once determined
            'name': 'EndpointNotFound',
            'message': 'Server failed to find the requested endpoint'
        }), 404


@mod.app_errorhandler(422)
def error422(e):
    """
    Returns the 422 error page

    :param e: HTTP error
    """

    return render_template('/errors/422.html'), 422


@mod.app_errorhandler(500)
def error500(e):
    """
    Returns the 500 error page

    :param e: HTTP error
    """

    return render_template('/errors/500.html'), 500


@mod.app_errorhandler(501)
def error501(e):
    """
    Returns the 501 error page

    :param e: HTTP error
    """

    return render_template('/errors/501.html'), 501


@mod.app_errorhandler(503)
def error503(e):
    """
    Returns the 503 error page

    :param e: HTTP error
    """

    return render_template('/errors/503.html'), 503

