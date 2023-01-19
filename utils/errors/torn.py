# Copyright (C) 2021-2023 tiksan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


_tornerrors = {
    0: ("Unknown error", "Unhandled error, should not occur."),
    1: ("Key is empty", "Private key is empty in current request."),
    2: ("Incorrect key", "Private key is wrong/incorrect format"),
    3: ("Wrong type", "Requesting an incorrect basic type"),
    4: ("Wrong fields", "Requesting incorrect selection fields"),
    5: (
        "Too many requests",
        "Requests are blocked for a small time because of too many requests per user (max 100 per minute).",
    ),
    6: ("Incorrect ID", "Wrong ID value"),
    7: ("Incorrect ID-entity relationship", "A requested selection is private."),
    8: (
        "IP block",
        "Current IP is banned for a small period of time because of abuse.",
    ),
    9: ("API disabled", "API system is currently disabled."),
    10: (
        "Key owner is in federal jail",
        "Current key can't be used because owner is in federal jail.",
    ),
    11: ("Key change error", "You can only change your API key once every 60 seconds."),
    12: ("Key read error", "Error reading key from database."),
    13: (
        "The key is temporarily disabled due to owner inactivity",
        "The key owner hasn't been online for more than 7 days.",
    ),
    14: (
        "Daily read limit reached",
        "Too many records have been pulled today by this user from our cloud services.",
    ),
    15: (
        "Temporary error",
        "An error code specifically for testing purposes that has no dedicated meaning.",
    ),
    16: (
        "Access level of this key is not high enough",
        "A selection is being called of which this key does not have permission to access.",
    ),
    17: ("Backend error occurred", "Please try again."),
}


class MissingKeyError(Exception):
    pass


class TornError(Exception):
    def __init__(self, code: int, endpoint: str):
        super().__init__()

        self.code = code
        self.endpoint = endpoint
        self.error, self.message = _tornerrors[code] if code in _tornerrors else (None, None)

    def __str__(self):
        return f"The Torn API has returned error code {self.code}"

    def __reduce__(self):
        return self.__class__, (self.code, self.endpoint)
