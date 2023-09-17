--[[
Copyright (C) 2021-2023 tiksan

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
--]]

-- Utilized by DBucket.call()
--
-- Verifies that the call is above the global and per-route ratelimit and decrements relevant call remaining counters.
--
-- KEYS[1] -> key for calls remaining on route
-- KEYS[2] -> key for route limit
-- KEYS[3] -> key for global ratelimit
--
-- Returns false if call is rate-limited
-- Returns [remaining, limit, expire] if call is OK
--
-- NOTE: redis.call("GET", ...) == false states that the key doesn't exist

-- Sets the global ratelimit if doesn't exist
redis.call("SET", KEYS[3], 49, "NX", "EX", 60)

local remaining = redis.call("GET", KEYS[1])

-- Retrieve per-route limit
local limit = redis.call("GET", KEYS[2])

if limit == false then
    limit = 1
    remaining = 1
    redis.call("SET", KEYS[1], limit, "NX", "EX", 2)
else
    limit = tonumber(limit)
end

if remaining ~= false then
    remaining = tonumber(remaining)
end

if remaining == false then
    redis.call("SET", KEYS[1], limit - 1, "NX", "EX", tonumber(redis.call("TIME")[1]))
    remaining = limit - 1
elseif remaining < 1 then
    return false
else
    redis.call("DECR", KEYS[1])
end

-- OK
return {
    remaining,
    limit,
    tonumber(redis.call("TTL", KEYS[1]))
}