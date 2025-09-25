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
  Map the overdose data to `Tornium.Schema.OverdoseCount`.
  """
  @spec map_counts(overdose_data :: [FactionContributor.t()], faction_id :: integer()) :: [
          %{faction_id: integer(), user_id: integer(), count: integer(), updated_at: DateTime.t()}
        ]
  def map_counts([%FactionContributor{} | _] = overdose_data, faction_id) when is_integer(faction_id) do
    overdose_data
    |> counts()
    |> Enum.map(fn {member_id, overdose_count} ->
      %{
        guid: Ecto.UUID.generate(),
        faction_id: faction_id,
        user_id: member_id,
        count: overdose_count,
        updated_at: DateTime.utc_now(:second)
      }
    end)
  end

  @doc """
  Map the updated overdose counts to `Tornium.Schema.OverdoseEvent`.
  """
  @spec map_events(overdosed_members :: [Tornium.Schema.OverdoseCount.t()], faction_id :: integer()) :: [
          %{faction_id: integer(), user_id: integer(), created_at: DateTime.t(), drug: term()}
        ]
  def map_events([%Tornium.Schema.OverdoseCount{} | _] = overdosed_members, faction_id) when is_integer(faction_id) do
    # TODO: Determine the drug used
    # TODO: Test this

    Enum.map(overdosed_members, fn %Tornium.Schema.OverdoseCount{user_id: member_id} when is_integer(member_id) ->
      %{
        guid: Ecto.UUID.generate(),
        faction_id: faction_id,
        user_id: member_id,
        created_at: DateTime.utc_now(:second),
        drug: nil
      }
    end)
  end

  def map_events([] = _overdosed_members, faction_id) when is_integer(faction_id) do
    []
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
      timestamp: DateTime.utc_now(:second) |> DateTime.to_iso8601()
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
      timestamp: DateTime.utc_now(:second) |> DateTime.to_iso8601()
    }
  end

  @doc """
  Generate a Discord embed reporting all overdoses for a day.

  If the overdose event has a known drug used, the drug will be included in the embed.
  """
  @spec to_report_embed(events :: [Tornium.Schema.OverdoseEvent.t()], faction_name :: String.t()) ::
          Nostrum.Struct.Embed.t()
  def to_report_embed(events, faction_name) when events == [] and is_binary(faction_name) do
    %Nostrum.Struct.Embed{
      title: "Overdose Report for #{faction_name}",
      description: "No overdoses recorded.",
      timestamp: DateTime.utc_now(:second) |> DateTime.to_iso8601()
    }
  end

  def to_report_embed(events, faction_name) when is_list(events) and is_binary(faction_name) do
    %Nostrum.Struct.Embed{
      title: "Overdose Report for #{faction_name}",
      description: "",
      timestamp: DateTime.utc_now(:second) |> DateTime.to_iso8601()
    }
    |> do_to_report_embed(events)
  end

  defp do_to_report_embed(%Nostrum.Struct.Embed{description: description} = embed, [
         %Tornium.Schema.OverdoseEvent{
           drug: drug,
           created_at: created_at,
           user: %Tornium.Schema.User{tid: user_tid, name: user_name}
         }
         | remaining_events
       ])
       when is_nil(drug) do
    embed
    |> Map.replace(
      :description,
      description <>
        "\n#{user_name} [#{user_tid}]: #{DateTime.to_iso8601(created_at)} (on unknown)"
    )
    |> do_to_report_embed(remaining_events)
  end

  defp do_to_report_embed(%Nostrum.Struct.Embed{description: description} = embed, [
         %Tornium.Schema.OverdoseEvent{
           drug: drug,
           created_at: created_at,
           user: %Tornium.Schema.User{tid: user_tid, name: user_name}
         }
         | remaining_events
       ])
       when is_binary(drug) do
    embed
    |> Map.replace(
      :description,
      description <>
        "\n#{user_name} [#{user_tid}]: #{DateTime.to_iso8601(created_at)} (on #{drug})"
    )
    |> do_to_report_embed(remaining_events)
  end

  defp do_to_report_embed(%Nostrum.Struct.Embed{} = embed, []) do
    embed
  end
end
