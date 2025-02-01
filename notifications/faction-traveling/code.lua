-- `faction` is the API response for the series of selections used
---@class Faction
---@field members table<string, table>
---@field name string
faction = faction

---@class FlyingMember
---@field tid integer|string
---@field name string
---@field earliest_departure_time integer?
---@field landed boolean?
---@field status table?
---@field origin string?

---@class State
---@field members table<string, table<string, FlyingMember>>
---@field last_update_time integer
---@field initialized boolean
state = state
-- TODO: Reset notification states when the code is updated

if state.members == nil then
  state.members = {}
end

local destination_travel_durations = {
  -- Destination: [Standard, Airstrip, WLT, BCT]
  ["Mexico"] = { 1560, 1080, 780, 480 },
  ["Cayman Islands"] = { 2100, 1500, 1080, 660 },
  ["Canada"] = { 2460, 1740, 1200, 720 },
  ["Hawaii"] = { 8040, 5460, 4020, 2400 },
  ["United Kingdom"] = { 9540, 6660, 4800, 2880 },
  ["Argentina"] = { 10020, 7020, 4980, 3000 },
  ["Switzerland"] = { 10500, 7380, 5280, 3180 },
  ["Japan"] = { 13500, 9480, 6780, 4080 },
  ["China"] = { 14520, 10140, 7260, 4320 },
  ["UAE"] = { 16260, 11400, 8100, 4860 },
  ["South Africa"] = { 17820, 12480, 8940, 5340 },
}

function string.split(match_string)
  local ret_table = {}

  for token in string.gmatch(match_string, "%S+") do
    table.insert(ret_table, token)
  end

  return ret_table
end

function string.starts_with(match_string, starts)
  return string.sub(match_string, 1, #starts) == starts
end

function string.gmatch(str, pattern)
  -- Used to override gmatch implementation that isn't implemented in luerl
  -- Taken from https://github.com/rvirding/luerl/issues/150

  local callable = {
    nextPos = 0,
    str = str,
    pattern = pattern
  }
  local mt = {}

  function mt.__call(table)
    local match_start, match_end = string.find(table.str, table.pattern, table.nextPos)

    if (match_start == nil) then
      return nil;
    else
      table.nextPos = match_end + 1;
      return string.sub(table.str, match_start, match_end)
    end
  end

  setmetatable(callable, mt)
  return callable
end

function table.join(tbl, seperator)
  local ret_string = ""

  for i, token in pairs(tbl) do
    if i == 1 then
      ret_string = token
    else
      ret_string = ret_string .. seperator .. token
    end
  end

  return ret_string
end

function table.find(tbl, expected_value)
  for index, value in ipairs(tbl) do
    if value == expected_value then
      return index
    end
  end

  return nil
end

--- Try to insert data into a table of table
---@param tbl table<string, table>
---@param key string
---@param value any
local function try_insert_table(tbl, key, value)
  if not tbl[key] then
    tbl[key] = {}
  end

  tbl[key][value.tid] = value
end

--- Extract the destination string from a user's status
---@param status_string string user.status.description
---@return string? "Destination of the user (or current location if abroad)"
local function get_destination(status_string)
  local destination_words = string.split(status_string)

  if string.starts_with(status_string, "Traveling") then
    return table.join({ table.unpack(destination_words, 3, #destination_words) }, " ")
  elseif string.starts_with(status_string, "Returning to Torn") then
    return "Torn"
  elseif string.starts_with(status_string, "In") and string.find(status_string, "hospital") ~= nil then
    local hospital_index = table.find(destination_words, "hospital")
    return table.join({ table.unpack(destination_words, 3, hospital_index) }, " ")
  elseif string.starts_with(status_string, "In") then
    return table.join({ table.unpack(destination_words, 2, #destination_words) }, " ")
  end

  return nil
end

--- Extract the origin string from a user's status when the user is returning to Torn from that origin
---@param status_string string user.status.description
---@return string? "Destination of the user (or current location if abroad)"
function get_origin(status_string)
  if string.starts_with(status_string, "Returning to Torn") then
    local destination_words = string.split(status_string)
    return table.join({ table.unpack(destination_words, 5, #destination_words) }, " ")
  end

  return nil
end

--- Format the username for a member
---@param member FlyingMember
---@return string Formatted member string
local function format_username(member)
  return string.format("%s [%d]", member.name, member.tid)
end

--- Remove a member from all destinations other than where they are
---@param member_id string
---@param destination string
local function remove_member_other_destinations(member_id, destination)
  for iter_destination, destination_members in pairs(state.members) do
    if destination_members[member_id] and iter_destination ~= destination then
      state.members[iter_destination][member_id] = nil
    end
  end
end

-- Iterate over the faction members
for member_id, member_data in pairs(faction.members) do
  local destination = get_destination(member_data.status.description)
  remove_member_other_destinations(member_id, destination)

  ---@type FlyingMember
  local member_table = {
    tid = member_id,
    name = member_data.name,
  }

  if string.starts_with(member_data.status.description, "In hospital") or string.starts_with(member_data.status.description, "In jail") then
    -- e.g. "In hospital for 4 mins "
    destination = nil
  elseif string.starts_with(member_data.status.description, "Traveling") then
    -- The faction member is flying
    member_table.landed = false
    member_table.status = nil

    if state.initialized and state.members[destination] and state.members[destination][member_id] and state.members[destination][member_id].earliest_departure_time then
      -- A departure time already exists and shouldn't be updated
      member_table.earliest_departure_time = state.members[destination][member_id].earliest_departure_time
    elseif state.initialized and (not state.members[destination] or not state.members[destination][member_id]) then
      -- A departure time doesn't exist and the current time should be used instead
      member_table.earliest_departure_time = math.floor(os.time(os.date("!*t")))
    else
      member_table.earliest_departure_time = nil
    end
  elseif string.starts_with(member_data.status.description, "Returning") then
    -- The faction member is flying back to Torn
    member_table.landed = false
    member_table.status = nil
    member_table.origin = get_origin(member_data.status.description)

    if state.initialized and state.members[destination] and state.members[destination][member_id] and state.members[destination][member_id].earliest_departure_time then
      -- A departure time already exists and shouldn't be updated
      member_table.earliest_departure_time = state.members[destination][member_id].earliest_departure_time
    elseif state.initialized and (not state.members[destination] or not state.members[destination][member_id]) then
      -- A departure time doesn't exist and the current time should be used instead
      member_table.earliest_departure_time = math.floor(os.time(os.date("!*t")))
    else
      member_table.earliest_departure_time = nil
    end
  elseif member_data.status.state == "Abroad" then
    -- The faction member is abroad in a certain country
    member_table.status = nil
    member_table.landed = true
    member_table.earliest_departure_time = nil
  elseif member_data.status.state == "Hospital" and string.starts_with(member_data.status.description, "In a") and string.find(member_data.status.description, "hospital") then
    -- The faction member is in an hospital abroad
    member_table.status = member_data.status
    member_table.landed = true
    member_table.earliest_departure_time = nil
  end

  if destination ~= nil then
    try_insert_table(state.members, destination, member_table)
  end
end

local render_state = {
  faction_name = faction.name,
  flying_members = {},
  hospital_members = {},
  abroad_members = {},
}

for destination, destination_members in pairs(state.members) do
  for _, member in pairs(destination_members) do
    if member.landed and member.status ~= nil then
      try_insert_table(render_state.hospital_members, destination, {
        tid = member.tid,
        username = format_username(member),
        status = member.status,
      })
    elseif member.landed then
      try_insert_table(render_state.abroad_members, destination, {
        tid = member.tid,
        username = format_username(member),
      })
    else
      local regular_landing = nil
      if member.earliest_departure_time and destination_travel_durations[member.origin or destination] then
        regular_landing = member.earliest_departure_time + destination_travel_durations[member.origin or destination][1]
      end

      try_insert_table(render_state.flying_members, destination, {
        tid = member.tid,
        username = format_username(member),
        regular_landing = regular_landing,
      })
    end
  end
end

if not state.initialized then
  -- If `state.initialized` is nil or false, the data required for this is not initialized in the database
  -- and people already flying will have inaccurate flight landing times calculated
  state.initialized = true
end

-- For simplicity, the message will always be updated to avoid issues with data changing between API calls
return true, render_state, state
