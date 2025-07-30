---@alias memberStatus {until: integer | nil, state: string, details: string | nil, description: string}
---@alias member {status: memberStatus, name: string, id: integer}

-- `faction` is the API response for the series of selections used
---@class Faction
---@field members member[]
faction = faction

---@class State
state = state

function string.starts_with(match_string, starts)
  return string.sub(match_string, 1, #starts) == starts
end

local members_leaving_hosp = {}
local leaving_hospital_count = 0
local now_timestamp = os.time(os.date("!*t"))

---@param member member
local function is_leaving_hosp(member)
  if member.status.state ~= "Hospital" then
    -- Member is not in the hospital
    return false
  elseif member.status.description == nil then
    -- This state should never be reached. There should always be an status description when a user is in the hospital.
    return false
  elseif not string.starts_with(member.status.description, "In hospital") then
    -- Member is in the hospital abroad
    return false
  elseif member.status["until"] == nil then
    -- This state should never be reached. There should always be an until timestamp when a user is in the hospital.
    return false
  elseif member.status["until"] - now_timestamp < 0 then
    -- Member has already left the hospital by the time the data has been processed
    return false
  elseif member.status["until"] - now_timestamp > 600 then
    -- Member is leaving the hospital in more than ten minutes
    return false
  else
    return true
  end
end

for _, member in ipairs(faction.members) do
  if is_leaving_hosp(member) then
    leaving_hospital_count = leaving_hospital_count + 1

    members_leaving_hosp[leaving_hospital_count] = member
  end
end

-- Sort the hospitalized members by earliest leaving the hospital
table.sort(members_leaving_hosp, function (a, b)
  return a.status["until"] < b.status["until"]
end)

local render_state = {
  faction_name = faction.name,
  members_leaving_hosp = members_leaving_hosp
}

return leaving_hospital_count ~= 0, render_state, state
