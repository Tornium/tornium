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

from tornium_commons import rds
from tornium_commons.models import ItemModel

from controllers.api.decorators import authentication_required, ratelimit
from controllers.api.utils import api_ratelimit_response, make_exception_response


@authentication_required
@ratelimit
def item_name_map(*args, **kwargs):
    key = f"tornium:ratelimit:{kwargs['user'].tid}"
    redis_client = rds()

    torn_items = redis_client.hgetall("tornium:items:name-map")

    if len(torn_items) == 0:
        torn_items = {item.tid: item.name for item in ItemModel.objects().only("tid", "name")}

        if len(torn_items) == 0:
            return make_exception_response("1000", key, details={"element": "torn_items"})

        redis_client.hset("tornium:items:name-map", mapping=torn_items)
        redis_client.expire("tornium:items:name-map", 3600)

    return {"items": torn_items}, 200, api_ratelimit_response(key)
