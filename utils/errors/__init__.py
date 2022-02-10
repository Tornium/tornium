# This file is part of Tornium.
#
# Tornium is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tornium is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Tornium.  If not, see <https://www.gnu.org/licenses/>.


_httperrors = {
    100: 'Continue',
    101: 'Switching Protocols',
    102: 'Processing',
    200: 'OK',
    201: 'Created',
    202: 'Accepted',
    203: 'Non-authoritative Information',
    204: 'No Content',
    205: 'Reset Content',
    206: 'Partial Content',
    207: 'Multi-Status',
    208: 'Already Reported',
    226: 'IM Used',
    300: 'Multiple Choices',
    301: 'Moved Permanently',
    302: 'Found',
    303: 'See Other',
    304: 'Not Modified',
    305: 'Use Proxy',
    307: 'Temporary Redirect',
    308: 'Permanent Redirect',
    400: 'Bad Request',
    401: 'Unauthorized',
    402: 'Payment Required',
    403: 'Forbidden',
    404: 'Not Found',
    405: 'Method Not Found',
    406: 'Not Acceptable',
    407: 'Proxy Authentication Required',
    408: 'Request Timeout',
    409: 'Conflict',
    410: 'Gone',
    411: 'Length Required',
    412: 'Precondition Failed',
    413: 'Payload Too Large',
    414: 'Request-URI Too Long',
    415: 'Unsupported Media Type',
    416: 'Requested Range Not Satisfiable',
    417: 'Expectation Failed',
    418: 'I\'m a teapot',
    421: 'Misdirected Request',
    422: 'Unprocessable Entity',
    423: 'Locked',
    424: 'Failed Dependency',
    426: 'Upgrade Required',
    428: 'Precondition Required',
    429: 'Too Many Requests',
    431: 'Request Header Fields Too Large',
    444: 'Connection Closed Without Resopnse',
    451: 'Unavailable For Legal Reasons',
    499: 'Client Closed Request',
    500: 'Internal Server Error',
    501: 'Not Implemented',
    502: 'Bad Gateway',
    503: 'Service Unavailable',
    504: 'Gateway Timeout',
    505: 'HTTP Version Not Supported',
    506: 'Variant Also Negotiates',
    507: 'Insufficient Storage',
    508: 'Loop Detected',
    510: 'Not Extended',
    511: 'Network Authentication Required',
    599: 'Network Connect Timeout Error'
}


class NetworkingError(Exception):
    def __init__(self, code: int):
        super().__init__()

        self.code = code
        self.message = _httperrors.get(self.code) if self.code in _httperrors else self.code


class TornError(Exception):
    def __init__(self, code: int):
        super().__init__()

        self.code = code

        if self.code == 0:
            self.error = 'Unknown error'
            self.message = 'Unhandled error, should not occur.'
        elif self.code == 1:
            self.error = 'Key is empty'
            self.message = 'Private key is empty in current request.'
        elif self.code == 2:
            self.error = 'Incorrect key'
            self.message = 'Private key is wrong/incorrect format.'
        elif self.code == 3:
            self.error = 'Wrong type'
            self.message = 'Requesting an incorrect basic type.'
        elif self.code == 4:
            self.error = 'Wrong fields'
            self.message = 'Requesting incorrect selection fields.'
        elif self.code == 5:
            self.error = 'Too many requests'
            self.message = 'Requests are blocked for a small period of time because of too many requests per user (max 100 per minute).'
        elif self.code == 6:
            self.error = 'Incorrect ID'
            self.message = 'Wrong ID value.'
        elif self.code == 7:
            self.error = 'Incorrect ID-entity relation'
            self.message = 'A requested selection is private (For example, personal data of another user / faction).'
        elif self.code == 8:
            self.error = 'IP block'
            self.message = 'Current IP is banned for a small period of time because of abuse.'
        elif self.code == 9:
            self.error = 'API disabled'
            self.message = 'API system is currently disabled.'
        elif self.code == 10:
            self.error = 'Key owner is in federal jail'
            self.message = 'Current key can\'t be used because owner is in federal jail.'
        elif self.code == 11:
            self.error = 'Key change error'
            self.message = 'You can only change your API key once every 60 seconds.'
        elif self.code == 12:
            self.error = 'Key read error'
            self.message = 'Error reading key from database.'
        elif self.code == 13:
            self.error = 'The key is temporarily disabled due to owner inactivity'
            self.message = 'The key owner hasn\'t been online for more than 7 days.'
        elif self.code == 14:
            self.error = 'Daily read limit reached'
            self.message = 'Too many records have been pulled today by this user from our cloud services.'
        elif self.code == 15:
            self.error = 'Temporary error'
            self.message = 'An error code specifically for testing purposes that has no dedicated meaning.'
        elif self.code == 16:
            self.error = 'Access level of this key is not high enough'
            self.message = 'A selection is being called of which this key does not have permission to access.'
        else:
            raise ValueError(f'Illegal Torn error code {code}')


class DiscordError(Exception):
    def __init__(self, code, message):
        super().__init__()

        self.code = code
        self.message = message


class MissingKeyError(Exception):
    pass


class RatelimitError(Exception):
    pass
