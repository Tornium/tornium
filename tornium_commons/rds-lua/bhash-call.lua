if redis.call("SET", KEYS[3], 49, "NX", "EX", 60) == "OK" then
    return 1
elseif tonumber(redis.call("GET", KEYS[3])) < 1 then
    return 1
end

local remaining = redis.call("GET", KEYS[1])
local limit = false

if remaining == false then
    if limit == false then
        limit = redis.call("GET", KEYS[2])

        if limit == false then
            limit = 1
        else
            limit = tonumber(limit)
        end
    end

    redis.call("SET", KEYS[1], limit, "NX", "EX", 2)
end

if redis.call("EXISTS", KEYS[1]) == "0" then
    if limit == false then
        limit = redis.call("GET", KEYS[2])

        if limit == false then
            limit = 1
        else
            limit = tonumber(limit)
        end
    end

    redis.call("SET", KEYS[1], limit - 1, "NX", "EX", 2)
elseif tonumber(redis.call("GET", KEYS[1])) < 1 then
    return 0
else
    redis.call("DECR", KEYS[1])
end

return 1