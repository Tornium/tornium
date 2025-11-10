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

  import Ecto.Query
  alias Torngen.Client.Schema.FactionContributor
  alias Tornium.Repo

  @typedoc """
  An overdose event map.
  """
  @type event :: %{
          faction_id: non_neg_integer(),
          user_id: non_neg_integer(),
          created_at: DateTime.t(),
          drug_id: non_neg_integer() | nil
        }

  @drug_items %{
    196 => "Cannabis",
    197 => "Ecstasy",
    198 => "Ketamine",
    199 => "LSD",
    200 => "Opium",
    201 => "PCP",
    203 => "Shrooms",
    204 => "Speed",
    205 => "Vicodin",
    206 => "Xanax",
    870 => "Love Juice"
  }
  @drug_item_ids @drug_items |> Map.keys()

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
  @spec map_events(overdosed_members :: [Tornium.Schema.OverdoseCount.t()], faction_id :: integer()) :: [event()]
  def map_events([%Tornium.Schema.OverdoseCount{} | _] = overdosed_members, faction_id) when is_integer(faction_id) do
    Enum.map(
      overdosed_members,
      fn %Tornium.Schema.OverdoseCount{user_id: member_id} when is_integer(member_id) ->
        %{
          guid: Ecto.UUID.generate(),
          faction_id: faction_id,
          user_id: member_id,
          created_at: DateTime.utc_now(:second),
          drug_id: nil
        }
      end
    )
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
          drug_id: drug_id,
          user: %Tornium.Schema.User{tid: user_id, name: user_name},
          faction: %Tornium.Schema.Faction{name: faction_name}
        } = _event
      )
      when is_nil(drug_id) do
    %Nostrum.Struct.Embed{
      title: "Member Overdosed",
      description:
        "User [#{user_name} [#{user_id}]](https://www.torn.com/profiles.php?XID=#{user_id}) of the faction #{faction_name} has overdosed on an unknown drug.",
      timestamp: DateTime.utc_now(:second) |> DateTime.to_iso8601()
    }
  end

  def to_embed(
        %Tornium.Schema.OverdoseEvent{
          drug_id: drug_id,
          user: %Tornium.Schema.User{tid: user_id, name: user_name},
          faction: %Tornium.Schema.Faction{name: faction_name}
        } = _event
      ) when is_integer(drug_id) do
    drug_name = Tornium.Item.NameCache.get_by_id(drug_id)

    %Nostrum.Struct.Embed{
      title: "Member Overdosed",
      description:
        "User [#{user_name} [#{user_id}]](https://www.torn.com/profiles.php?XID=#{user_id}) of the faction #{faction_name} has overdosed on #{drug_name}.",
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

  @doc """
  Attempt to determine the drug used in an overdose event.

  1) Check if there's a use event for the user in the faction armory logs.
  2) Check the user's logs if enabled and the user has a full access API key
  3) Set drug to `nil` as it is unknown.
  """
  @spec set_drug_used(event :: event(), overdose_last_updated :: DateTime.t() | nil) :: event()
  def set_drug_used(%{faction_id: faction_id, user_id: user_id, created_at: created_at} = event, overdose_last_updated)
      when not is_nil(overdose_last_updated) do
    armory_usage_logs =
      Tornium.Schema.ArmoryUsage
      |> where([u], u.faction_id == ^faction_id and u.user_id == ^user_id and u.item_id in @drug_item_ids)
      |> where([u], u.timestamp >= ^overdose_last_updated and u.timestamp <= ^created_at)
      |> Repo.all()

    case armory_usage_logs do
      [%Tornium.Schema.ArmoryUsage{item_id: item_id}] ->
        # Set the drug used from the armory usage log since there's only one potential drug used log
        Map.put(event, :drug_id, item_id)

      _ ->
        # One of the following is true:
        #  - There are no armory usage logs matching the timeframe
        #  - There are more than one logs matching the timeframe
        # 
        # Therefore, we should try to use the user's logs if we are able to.
        set_drug_used_logs(event, overdose_last_updated)
    end
  end

  def set_drug_used(event, overdose_last_updated) when is_map(event) and is_nil(overdose_last_updated) do
    event
  end

  @spec set_drug_used_logs(event :: event(), overdose_last_updated :: DateTime.t()) :: event()
  defp set_drug_used_logs(%{user_id: user_id, created_at: _created_at} = event, overdose_last_updated)
       when is_integer(user_id) do
    api_key = Tornium.User.Key.get_by_user(user_id)

    if Tornium.Schema.UserSettings.od_drug?(user_id) and not is_nil(api_key) and api_key.access_level == :full do
      # The user needs to have their `od_drug_enabled` set to true and to have a default full access API
      # key for this to pull their overdose logs.

      overdose_logs = get_user_overdoses(api_key, overdose_last_updated)

      case overdose_logs do
        [%Torngen.Client.Schema.UserLog{timestamp: overdosed_at, data: %{"item" => overdosed_item_id}}] ->
          event
          |> Map.put(:created_at, overdosed_at)
          |> Map.put(:drug_id, overdosed_item_id)

        _ ->
          # One of the following is true:
          #  - There are no overdose logs
          #  - The logs are of the wrong shape
          #  - There are more than one logs, so we can not be sure what drug the user overdosed on.
          Map.put(event, :drug_id, nil)
      end

      event
    else
      # Ensure the drug is set to `nil` so the armory usage logs can attempt to find a matching log
      # during its next run
      Map.put(event, :drug_id, nil)
    end
  end

  defp do_to_report_embed(%Nostrum.Struct.Embed{description: description} = embed, [
         %Tornium.Schema.OverdoseEvent{
           drug_id: drug_id,
           created_at: created_at,
           user: %Tornium.Schema.User{tid: user_tid, name: user_name}
         }
         | remaining_events
       ])
       when is_nil(drug_id) do
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
           drug_id: drug_id,
           created_at: created_at,
           user: %Tornium.Schema.User{tid: user_tid, name: user_name}
         }
         | remaining_events
       ]) when is_integer(drug_id) do
    drug_name = Tornium.Item.NameCache.get_by_id(drug_id)

    embed
    |> Map.replace(
      :description,
      description <>
        "\n#{user_name} [#{user_tid}]: #{DateTime.to_iso8601(created_at)} (on #{drug_name})"
    )
    |> do_to_report_embed(remaining_events)
  end

  defp do_to_report_embed(%Nostrum.Struct.Embed{} = embed, []) do
    embed
  end

  @doc """
  Get all overdose logs for a user.
  """
  @spec get_user_overdoses(api_key :: Tornium.Schema.TornKey.t(), from_timestamp :: DateTime.t()) :: [
          Torngen.Client.Schema.UserLog.t()
        ]
  def get_user_overdoses(%Tornium.Schema.TornKey{api_key: api_key} = _api_key, from_timestamp) do
    query =
      Tornex.SpecQuery.new(key: api_key)
      |> Tornex.SpecQuery.put_path(Torngen.Client.Path.User.Log)
      |> Tornex.SpecQuery.put_parameter(:log, [
        # Cannabis overdose
        2201,
        # Ecstacy overdose
        2211,
        # Ketamine overdose
        2221,
        # LSD overdose
        2231,
        # Opium overdose
        2241,
        # PCP overdose
        2251,
        # Shrooms overdose
        2261,
        # Speed overdose
        2281,
        # Vicodin overdose
        2281,
        # Xanax overdose
        2291
      ])
      |> Tornex.SpecQuery.put_parameter(:from, DateTime.to_unix(from_timestamp))
      |> Tornex.SpecQuery.put_parameter(:limit, 100)

    response = Tornex.API.get(query)

    case response do
      {:error, _error} ->
        []

      _ ->
        %{
          Torngen.Client.Path.User.Log => %{
            UserLogsResponse => %Torngen.Client.Schema.UserLogsResponse{
              log: logs
            }
          }
        } = Tornex.SpecQuery.parse(query, response)

        logs
    end
  end
end
