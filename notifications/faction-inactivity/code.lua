---@alias MemberStatus {color: "blue" | "green" | "red", until: integer, state: "Abroad" | "Fallen" | "Federal" | "Hospital" | "Jail" | "Okay" | "Traveling", details: string, description: string}
---@alias MemberLastAction {status: "Idle" | "Offline" | "Online", timestamp: integer, relative: string}
---@alias Member {status: MemberStatus, last_action: MemberLastAction, name: string, id: integer | nil, position: string}

-- `faction` is the API response for the series of selections used
---@class Faction
---@field members table<string, Member>
faction = faction

---@class State
state = state

-- Preprocessed variables
---@type number
DAYS = tonumber(DAYS) or 1

--- Format the username for a member
---@param member_id string
---@param member_name string
---@return string Formatted member string
local function format_username(member_id, member_name)
  return string.format("%s [%s]", member_name, member_id)
end

local minimum_seconds = DAYS * 24 * 60 * 60
local inactive_members = {}
local inactive_members_count = 0
local now_timestamp = math.floor(os.time(os.date("!*t")))

for member_id, member_data in pairs(faction.members) do
  local seconds_since_action = now_timestamp - member_data.last_action.timestamp

  if seconds_since_action >= minimum_seconds then
    inactive_members_count = inactive_members_count + 1
    table.insert(inactive_members, {
      id = member_id,
      fedded = member_data.status.state == "Federal",
      fedded_reason = member_data.status.description,
      recruit = member_data.position == "Recruit",
      username = format_username(member_id, member_data.name),
      last_action = member_data.last_action.timestamp
    })
  end
end

local render_state = {
  faction_name = faction.name,
  configured_days = DAYS,
  inactive_members = inactive_members
}

return inactive_members_count ~= 0, render_state, state
