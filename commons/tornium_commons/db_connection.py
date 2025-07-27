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

from functools import wraps

from playhouse.pool import PooledPostgresqlExtDatabase

from .config import Config

db = PooledPostgresqlExtDatabase(None)


def init_db() -> None:
    _s = Config.from_json()
    db.init("Tornium", max_connections=16, stale_timeout=300, dsn=_s.db_dsn.unicode_string())


def with_db_connection(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            if db.is_closed():
                db.connect()

            return f(*args, **kwargs)
        finally:
            if not db.is_closed():
                db.close()

    return wrapper
