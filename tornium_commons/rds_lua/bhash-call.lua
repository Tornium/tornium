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
-- Returns 0 if call is rate-limited
-- Returns 1 if call is OK
--
-- NOTE: redis.call("GET", ...) == false states that the key doesn't exist

-- Sets the global ratelimit if doesn't exist
if redis.call("SET", KEYS[3], 49, "NX", "EX", 60) == "OK" then
    return 1
-- Verifies global ratelimit
elseif tonumber(redis.call("GET", KEYS[3])) < 1 then
    return 1
end

local limit = false  -- per-route ratelimit limit

-- Checks
if redis.call("EXISTS", KEYS[1]) == "0" then
    if limit == false then
        limit = redis.call("GET", KEYS[2])

        if limit == false then
            limit = 1
        else
            limit = tonumber(limit)
        end
    end

    -- Set calls remaining from limit
    redis.call("SET", KEYS[1], limit - 1, "NX", "EX", 2)
elseif tonumber(redis.call("GET", KEYS[1])) < 1 then
    -- Call rate-limited from pre-route ratelimit
    return 0
else
    -- Per-route ratelimit remaining decrement
    redis.call("DECR", KEYS[1])
end

return 1  -- OK