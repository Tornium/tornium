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

import time
import typing

import redis
from flask import jsonify
from tornium_commons import rds

API_EXCEPTIONS = {
    "0000": {
        "code": 0,
        "name": "GeneralError",
        "http": 400,
        "message": "Something bad happened.",
        "details": None,
    },
    "0001": {
        "code": 1,
        "name": "OK",
        "http": 200,
        "message": "Server request was successful.",
        "details": None,
    },
    "0002": {
        "code": 2,
        "name": "Partially OK",
        "http": 200,
        "message": "Server request was partially successful.",
        "details": None,
    },
    "1000": {
        "code": 1000,
        "name": "UnknownElement",
        "http": 400,
        "message": "Server failed to respond. An un-caught element could not be located.",
        "details": None,
    },
    "1001": {
        "code": 1001,
        "name": "UnknownGuild",
        "http": 404,
        "message": "Server failed to locate the requested Discord guild.",
    },
    "1002": {
        "code": 1002,
        "name": "UnknownChannel",
        "http": 404,
        "message": "Server failed to locate the requested Discord channel",
    },
    "1003": {
        "code": 1003,
        "name": "UnknownRole",
        "http": 404,
        "message": "Server failed to locate the requested Discord role.",
    },
    "1004": {
        "code": 1004,
        "name": "UnknownMember",
        "http": 404,
        "message": "Server failed to locate the requested Discord member.",
    },
    "1100": {
        "code": 1100,
        "name": "UnknownUser",
        "http": 404,
        "message": "Server failed to locate the requested Torn user.",
    },
    "1101": {
        "code": 1101,
        "name": "UnknownCompany",
        "http": 404,
        "message": "Server failed to locate the requested Torn company.",
    },
    "1102": {
        "code": 1102,
        "name": "UnknownFaction",
        "http": 404,
        "message": "Server failed to locate the requested Torn faction.",
    },
    "1103": {
        "code": 1103,
        "name": "UnknownPosition",
        "http": 404,
        "message": "Server failed to locate the requested Torn faction position.",
    },
    "1104": {
        "code": 1104,
        "name": "UnknownItem",
        "http": 404,
        "message": "Server failed to locate the requested Torn item.",
    },
    "1105": {
        "code": 1105,
        "name": "UnknownOrganizedCrime",
        "http": 404,
        "message": "Server failed to locate the requested Torn organized crime.",
    },
    "1106": {
        "code": 1106,
        "name": "UnknownOrganizedCrimeTeam",
        "http": 404,
        "messsage": "Server failed to located the requested organized crime team.",
    },
    "1107": {
        "code": 1107,
        "name": "UnknownOrganizedCrimeTeamMember",
        "http": 404,
        "message": "Server failed to locate the requested organized crime team member.",
    },
    "1200": {
        "code": 1200,
        "name": "UnknownKey",
        "http": 404,
        "message": "Server failed to locate a Torn API key.",
    },
    "1201": {
        "code": 1201,
        "name": "UnknownFactionKey",
        "http": 404,
        "message": "Server failed to locate a Torn faction AA API key.",
    },
    "1300": {
        "code": 1300,
        "name": "UnknownGatewayClient",
        "http": 404,
        "message": "[DEPRECATED] Server failed to locate the requested gateway client.",
    },
    "1400": {
        "code": 1400,
        "name": "UnknownNotificationTrigger",
        "http": 404,
        "message": "Server failed to locate the requested notification trigger.",
    },
    "1401": {
        "code": 1401,
        "name": "UnknownNotification",
        "http": 400,
        "message": "Server failed to locate the requested notification.",
    },
    "1402": {
        "code": 1402,
        "name": "UnknownNotificationParameters",
        "http": 404,
        "message": "Server failed to locate the parameters or a specific parameter for the notification trigger.",
    },
    "1500": {
        "code": 1500,
        "name": "UnknownOAuthClient",
        "http": 404,
        "message": "Server failed to locate the request OAuth client.",
    },
    "4000": {
        "code": 4000,
        "name": "TooManyRequests",
        "http": 429,
        "message": "Too many requests were received from this user/scope.",
    },
    "4001": {
        "code": 4001,
        "name": "NoAuthenticationInformation",
        "http": 401,
        "message": "No authentication code was provided.",
    },
    "4002": {
        "code": 4002,
        "name": "InvalidAuthenticationInformation",
        "http": 401,
        "message": "The provided authentication code was invalid.",
    },
    "4003": {
        "code": 4003,
        "name": "InvalidAuthenticationType",
        "http": 401,
        "message": "The provided authentication type was invalid for the required authentication for the endpoint.",
    },
    "4004": {
        "code": 4004,
        "name": "InsufficientPermissions",
        "http": 403,
        "message": "The scope of the Tornium key provided was not sufficient for the request.",
    },
    "4005": {
        "code": 4005,
        "name": "InsufficientFactionPermissions",
        "http": 403,
        "message": "The provided authentication code was not sufficient for an AA level request.",
    },
    "4006": {
        "code": 4006,
        "name": "InsufficientFactionPermissions",
        "http": 403,
        "message": "The provided authentication code was not sufficient for a MC level request.",
    },
    "4010": {
        "code": 4010,
        "name": "EndpointNotFound",
        "http": 404,
        "message": "The requested endpoint is not registered.",
    },
    "4011": {
        "code": 4011,
        "name": "InvalidMethod",
        "http": 405,
        "message": "The requested endpoint does not support this HTTP method.",
    },
    "4020": {
        "code": 4020,
        "name": "InsufficientDiscordPermissions",
        "http": 403,
        "message": "The requesting user is not an admin in the provided guild.",
    },
    "4021": {
        "code": 4021,
        "name": "InsufficientDiscordFactionPermissions",
        "http": 403,
        "message": "The faction and/or guild do not have sufficient permissions for this operation.",
    },
    "4022": {
        "code": 4022,
        "name": "InsufficientResourcePermissions",
        "http": 403,
        "message": "The requesting user does not have sufficient permissions to access/modify this resource",
    },
    "4100": {
        "code": 4100,
        "name": "TornError",
        "http": 400,
        "message": "The Torn API has returned an error.",
        "details": None,
    },
    "4101": {
        "code": 4101,
        "name": "TornNetworkingError",
        "http": 400,
        "message": "The Torn API has returned a networking error.",
        "details": None,
    },
    "4102": {
        "code": 4102,
        "name": "DiscordNetworkingError",
        "http": 400,
        "message": "The Discord API has returned a networking error.",
        "details": None,
    },
    "4103": {
        "code": 4103,
        "name": "NetworkingError",
        "http": 400,
        "message": "An unknown API has returned a networking error.",
        "details": None,
    },
    "4290": {
        "code": 4290,
        "name": "GeneralRatelimit",
        "http": 429,
        "message": "User has reached a general ratelimit.",
    },
    "4291": {
        "code": 4291,
        "name": "AssistRatelimit",
        "http": 429,
        "message": "[DEPRECATED] User has reached a ratelimit on assists.",
    },
    "4292": {
        "code": 4292,
        "name": "BankingRatelimit",
        "http": 429,
        "message": "[DEPRECATED] User has reached a ratelimit on banking.",
    },
    "4300": {"code": 4300, "name": "OCMigrationError", "message": "Faction has not migrated to OCs 2.0."},
    "5000": {
        "code": 5000,
        "name": "BackendError",
        "http": 500,
        "message": "The backend has encountered an internal error.",
    },
}


def json_api_exception(code: str, details=None):
    if code not in API_EXCEPTIONS:
        raise Exception(f"Unknown API code {code} raised")

    exception = API_EXCEPTIONS[code]

    if "details" in exception and details is not None:
        exception["details"] = details

    return exception


def api_ratelimit_response(ratelimit_key: str, client: redis.Redis = None):
    if client is None:
        client = rds()

    try:
        return {
            "X-RateLimit-Limit": 250,
            "X-RateLimit-Remaining": 250 - int(client.get(ratelimit_key)),
            "X-RateLimit-Reset": client.ttl(ratelimit_key),
        }
    except TypeError:
        # The API call was made just before the end of the minute, and this code rolls over to the following minute
        expires_at = int(time.time()) // 60 * 60 + 60
        client.expireat(ratelimit_key, expires_at)

        return {
            "X-RateLimit-Limit": 250,
            "X-RateLimit-Remaining": 250,
            "X-RateLimit-Reset": expires_at,
        }


def make_exception_response(
    code: str,
    ratelimit_key: typing.Optional[str] = None,
    details=None,
    redis_client: redis.Redis = None,
):
    exception = json_api_exception(code, details)
    exception_response = {
        "code": exception["code"],
        "name": exception["name"],
        "message": exception["message"],
    }

    if "details" in exception:
        exception_response["details"] = exception["details"]

    if ratelimit_key is None:
        return jsonify(exception_response), exception["http"]
    else:
        return (
            jsonify(exception_response),
            exception["http"],
            api_ratelimit_response(ratelimit_key, redis_client),
        )


def get_list(data: dict, key: str, callable_type: typing.Callable | None) -> list:
    """
    Get a list of elements from a key in a dictionary. If a callable type is included, the values will be converted using that type.

    Based upon https://github.com/pallets/werkzeug/blob/7d67f88e6c8ed49ab205e2b6b208aede8b9b27d7/src/werkzeug/datastructures/headers.py#L164
    """

    if data.get(key) is None or len(data.get(key)) == 0:
        return []

    result = [value_part for value_part in data.get(key, "").split(",")]

    if callable_type is None:
        return result

    typed_result = []
    for value_part in result:
        try:
            typed_result.append(callable_type(value_part))
        except (TypeError, ValueError):
            continue

    return typed_result
