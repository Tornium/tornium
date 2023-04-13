local bhash = redis.call("GET", KEYS[1])

if bhash == false then
    redis.call("SET", KEYS[1] .. ":lock:" .. ARGV[1], 1, "NX", "EX", 2)
    return bhash
end

return bhash