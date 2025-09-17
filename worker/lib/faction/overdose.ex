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
  @moduledoc """
  Functions to collate overdose data.
  """

  alias Torngen.Client.Schema.FactionContributor

  @doc """
  Map the overdose count of faction members and their IDs.

  ## Examples

      iex> counts([
      ...>   %Torngen.Client.Schema.FactionContributor{in_faction: true, id: 1, value: 2},
      ...>   %Torngen.Client.Schema.FactionContributor{in_faction: false, id: 2, value: 3}
      ...> ])
      %{1 => 2}
  """
  @spec counts(overdose_data :: [FactionContributor.t()]) :: %{integer() => integer()}
  def counts([%FactionContributor{} | _] = overdose_data) do
    overdose_data
    |> Enum.filter(fn %FactionContributor{in_faction: in_faction} -> in_faction == true end)
    |> Enum.map(fn %FactionContributor{id: member_id, value: overdose_count} -> {member_id, overdose_count} end)
    |> Map.new()
  end

  @doc """
  Map the overdose data to `Tornium.Schema.OverdoseCount` without a count.

  This is intended to ensure new members get inserted to the database separately from the upsert.
  """
  @spec map_new_counts(overdose_data :: [FactionContributor.t()], faction_id :: integer()) :: [
          %{faction_id: integer(), user_id: integer(), count: integer(), updated_at: DateTime.t()}
        ]
  def map_new_counts([%FactionContributor{} | _] = overdose_data, faction_id) when is_integer(faction_id) do
    overdose_data
    |> counts()
    |> Enum.map(fn {member_id, _overdose_count} ->
      %{faction_id: faction_id, user_id: member_id, count: 0, updated_at: DateTime.utc_now()}
    end)
  end

  @doc """
  Map the overdose data to `Tornium.Schema.OverdoseCount`.
  """
  @spec map_counts(overdose_data :: [FactionContributor.t()], faction_id :: integer()) :: [
          %{faction_id: integer(), user_id: integer(), count: integer(), updated_at: DateTime.t()}
        ]
  def map_counts([%FactionContributor{} | _] = overdose_data, faction_id) when is_integer(faction_id) do
    overdose_data
    |> counts()
    |> Enum.map(fn {member_id, overdose_count} ->
      %{faction_id: faction_id, user_id: member_id, count: overdose_count, updated_at: DateTime.utc_now()}
    end)
  end

  @doc """
  Map the updated overdose counts to `Tornium.Schema.OverdoseEvent`.
  """
  @spec map_events(
          overdosed_members :: [Tornium.Schema.OverdoseCount.t()],
          faction_id :: integer(),
          new_member_ids :: [integer()]
        ) :: [%{faction_id: integer(), user_id: integer(), created_at: DateTime.t(), drug: term()}]
  def map_events([%Tornium.Schema.OverdoseCount{} | _] = overdosed_members, faction_id, new_member_ids)
      when is_integer(faction_id) and is_list(new_member_ids) do
    # TODO: Test this
    # TODO: Determine the drug used

    overdosed_members
    |> Enum.reject(fn %Tornium.Schema.OverdoseCount{user_id: member_id} when is_integer(member_id) ->
      Enum.member?(new_member_ids, member_id)
    end)
    |> Enum.map(fn %Tornium.Schema.OverdoseCount{user_id: member_id} when is_integer(member_id) ->
      %{faction_id: faction_id, user_id: member_id, created_at: DateTime.utc_now(), drug: nil}
    end)
  end

  @doc """
  Generate a Discord embed for the overdose event.

  If the overdose event has a known drug used, the drug will be included in the embed.
  """
  @spec to_embed(event :: Tornium.Schema.OverdoseEvent.t()) :: Nostrum.Struct.Embed.t()
  def to_embed(
        %Tornium.Schema.OverdoseEvent{
          drug: drug,
          user: %Tornium.Schema.User{tid: user_id, name: user_name},
          faction: %Tornium.Schema.Faction{name: faction_name}
        } = _event
      )
      when is_nil(drug) do
    %Nostrum.Struct.Embed{
      title: "Member Overdosed",
      description:
        "User [#{user_name} [#{user_id}]](https://www.torn.com/profiles.php?XID=#{user_id}) of the faction #{faction_name} has overdosed on an unknown drug.",
      timestamp: DateTime.utc_now() |> DateTime.to_iso8601()
    }
  end

  def to_embed(
        %Tornium.Schema.OverdoseEvent{
          drug: drug,
          user: %Tornium.Schema.User{tid: user_id, name: user_name},
          faction: %Tornium.Schema.Faction{name: faction_name}
        } = _event
      ) do
    %Nostrum.Struct.Embed{
      title: "Member Overdosed",
      description:
        "User [#{user_name} [#{user_id}]](https://www.torn.com/profiles.php?XID=#{user_id}) of the faction #{faction_name} has overdosed on #{drug}.",
      timestamp: DateTime.utc_now() |> DateTime.to_iso8601()
    }
  end
end
