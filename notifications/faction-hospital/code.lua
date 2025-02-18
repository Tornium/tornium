-- `faction` is the API response for the series of selections used
---@class Faction
---@field members table
---@field name string
faction = faction

---@class State
state = state

-- Preprocessed variables
---@type integer
MEMBER_LIMIT = MEMBER_LIMIT

local function format_username (user_id, user_name)
  return string.format("%s [%d]", user_name, user_id)
end

local hospitalized_members = {}

if faction == nil or faction.members == nil then
  return false, {}, state
end

-- Iterate over the faction members
for member_id, member_data in pairs(faction.members) do
  -- Check if the faction member is in the hospital
  if member_data.status.state == "Hospital" then
    table.insert(hospitalized_members, {id = member_id, timestamp = member_data.status["until"], username = format_username(member_id, member_data.name)})
  end
end

-- Sort the hospitalized members by earliest leaving the hospital
table.sort(hospitalized_members, function (a, b)
  return a.timestamp < b.timestamp
end)

local render_state = {
  faction_name = faction.name,
  hospitalized_members = hospitalized_members,
  member_limit = MEMBER_LIMIT
}

-- For simplicity, the message will always be updated to avoid issues with data changing between API calls
-- (e.g. someone leaving and re-entering the hospital within a minute)
return true, render_state, state
