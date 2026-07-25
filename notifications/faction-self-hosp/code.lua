---@alias MemberStatus {color: "blue" | "green" | "red", until: integer, state: "Abroad" | "Fallen" | "Federal" | "Hospital" | "Jail" | "Okay" | "Traveling", details: string, description: string}
---@alias Member {status: MemberStatus, name: string, id: integer | nil, discord: string | nil}
---@alias RankedWarStatus {start: integer, end: integer, target: integer, winner: integer}
---@alias RankedWar {war: RankedWarStatus}

-- `faction` is the API response for the series of selections used
---@class Faction
---@field members table<string, Member>
---@field ranked_wars table<string, RankedWar>
faction = faction

---@class State
---@field last_triggered table<string, integer>
state = state
state.last_triggered = state.last_triggered or {}

-- Preprocessed variables
---@type number
MINUTES = tonumber(MINUTES) or 5
---@type boolean
ONLY_RW = tornium.to_boolean(ONLY_RW) or false

function string.starts_with(match_string, starts)
  return string.sub(match_string, 1, #starts) == starts
end

local members_leaving_hosp = {}
local leaving_hospital_count = 0
local now_timestamp = math.floor(os.time(os.date("!*t")))

if ONLY_RW then
  local ranked_war_id, ranked_war = next(faction.ranked_wars)

  if ranked_war_id == nil or ranked_war == nil then
    return false, {}, state
  elseif ranked_war.war.start > now_timestamp then
    -- Ranked war has not begun yet
    return false, {}, state
  elseif ranked_war.war["end"] ~= 0 and ranked_war.war["end"] < now_timestamp then
    -- Ranked war has ended (equals 0 when the RW isn't over yet)
    return false, {}, state
  end
end

---@param member_id string
---@return boolean
local function should_trigger_member(member_id)
  local last_triggered = state.last_triggered[member_id]

  if last_triggered == nil then
    return true
  end

  return (now_timestamp - last_triggered) > MINUTES * 60
end

---@param member Member
---@return boolean
local function is_leaving_hosp(member)
  if member.status.state ~= "Hospital" then
    -- Member is not in the hospital
    return false
  elseif not string.starts_with(member.status.description, "In hospital") then
    -- Member is in the hospital abroad
    return false
  elseif member.status["until"] == 0 then
    -- This state should never be reached. There should always be an until timestamp when a user is in the hospital.
    return false
  elseif member.status["until"] - now_timestamp < 0 then
    -- Member has already left the hospital by the time the data has been processed
    return false
  elseif member.status["until"] - now_timestamp > MINUTES * 60 then
    -- Member is leaving the hospital in more than the specified number of minutes
    return false
  else
    return true
  end
end

for member_id, member in pairs(faction.members) do
  member.id = math.floor(tonumber(member_id))

  if is_leaving_hosp(member) and should_trigger_member(member_id) then
    leaving_hospital_count = leaving_hospital_count + 1
    local discord_id = tornium.get_discord_id(member.id)

    if discord_id == 0 or discord_id == nil then
      member.discord = ""
    else
      member.discord = "<@" .. discord_id .. ">"
    end

    members_leaving_hosp[leaving_hospital_count] = member
    state.last_triggered[member_id] = now_timestamp
  end
end

-- Sort the hospitalized members by earliest leaving the hospital
table.sort(members_leaving_hosp, function(a, b)
  return a.status["until"] < b.status["until"]
end)

-- TODO: Remove invalid keys that don't exist anymore and values that are too old

local render_state = {
  faction_name = faction.name,
  configured_minutes = MINUTES,
  members_leaving_hosp = members_leaving_hosp
}

return leaving_hospital_count ~= 0, render_state, state
