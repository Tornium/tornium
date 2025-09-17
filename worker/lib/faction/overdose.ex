# Copyright (C) 2021-2025 tiksan
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

defmodule Tornium.Faction.Overdose do
  alias Torngen.Client.Schema.FactionContributor

  def counts([%FactionContributor{} | _] = overdose_data) do
    overdose_data
    |> Enum.filter(fn %FactionContributor{in_faction: in_faction} -> in_faction == true end)
    |> Enum.map(fn %FactionContributor{id: member_id, value: overdose_count} -> {member_id, overdose_count} end)
    |> Map.new()
  end

  def map_new_counts([%FactionContributor{} | _] = overdose_data, faction_id) when is_integer(faction_id) do
    overdose_data
    |> counts()
    |> Enum.map(fn {member_id, _overdose_count} ->
      %{faction_id: faction_id, user_id: member_id, count: 0, updated_at: DateTime.utc_now()}
    end)
  end

  def map_counts([%FactionContributor{} | _] = overdose_data, faction_id) when is_integer(faction_id) do
    overdose_data
    |> counts()
    |> Enum.map(fn {member_id, overdose_count} ->
      %{faction_id: faction_id, user_id: member_id, count: overdose_count, updated_at: DateTime.utc_now()}
    end)
  end

  def map_events([%Tornium.Schema.OverdoseCount{} | _] = overdosed_members, faction_id, new_member_ids)
      when is_integer(faction_id) and is_list(new_member_ids) do
    overdosed_members
    |> Enum.reject(fn %Tornium.Schema.OverdoseCount{user_id: member_id} when is_integer(member_id) ->
      Enum.member?(new_member_ids, member_id)
    end)
    |> Enum.map(fn %Tornium.Schema.OverdoseCount{user_id: member_id} when is_integer(member_id) ->
      %{faction_id: faction_id, user_id: member_id, created_at: DateTime.utc_now(), drug: nil}
    end)
  end
end
