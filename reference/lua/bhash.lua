local bhash = redis.call("GET", KEYS[1])

if bhash == false then
    redis.call("SET", KEYS[1] .. ":lock", 1)
    return bhash
end

return bhash