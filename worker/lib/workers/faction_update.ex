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

defmodule Tornium.Workers.FactionUpdate do
  import Ecto.Query
  alias Tornium.Repo

  use Oban.Worker,
    max_attempts: 3,
    priority: 0,
    queue: :faction_processing,
    tags: ["faction"]

  @impl Oban.Worker
  def perform(
        %Oban.Job{
          args: %{
            "api_call_id" => api_call_id,
            "faction_id" => faction_id,
            "user_id" => user_id,
            "nonpublic?" => nonpublic?
          }
        } = _job
      ) do
    case Tornium.API.Store.pop(api_call_id) do
      nil ->
        {:cancel, :invalid_call_id}

      :expired ->
        {:cancel, :expired}

      :not_ready ->
        # This uses :error instead of :snooze to allow for an easy cap on the number of retries
        {:error, :not_ready}

      %{"error" => %{"code" => 7}} ->
        Tornium.Schema.User
        |> update([u], set: [faction_aa: false])
        |> where([u], u.tid == ^user_id)
        |> Repo.update_all([])

        :ok

      %{"error" => %{"code" => error_code}} when is_integer(error_code) ->
        {:cancel, {:api_error, error_code}}

      result when is_map(result) ->
        do_perform(result, faction_id, nonpublic?)
    end
  end

  @spec do_perform(api_call_result :: map(), faction_id :: non_neg_integer(), nonpublic? :: boolean()) ::
          Oban.Worker.result()
  defp do_perform(api_call_result, faction_id, true = _nonpublic?)
       when is_map(api_call_result) and is_integer(faction_id) do
    %{
      Torngen.Client.Path.Faction.Basic => %{
        FactionBasicResponse => %Torngen.Client.Schema.FactionBasicResponse{basic: basic_data}
      },
      Torngen.Client.Path.Faction.Members => %{
        FactionMembersResponse => %Torngen.Client.Schema.FactionMembersResponse{members: members_data}
      },
      Torngen.Client.Path.Faction.Positions => %{
        FactionPositionsResponse => %Torngen.Client.Schema.FactionPositionsResponse{positions: positions_data}
      }
    } =
      Tornex.SpecQuery.new()
      |> Tornex.SpecQuery.put_path(Torngen.Client.Path.Faction.Basic)
      |> Tornex.SpecQuery.put_path(Torngen.Client.Path.Faction.Members)
      |> Tornex.SpecQuery.put_path(Torngen.Client.Path.Faction.Positions)
      |> Tornex.SpecQuery.parse(api_call_result)

    Tornium.Schema.Faction.upsert(basic_data)

    positions = Tornium.Schema.FactionPosition.upsert_all(positions_data, faction_id)
    members = Tornium.Schema.Faction.upsert_members(members_data, positions, faction_id)

    Tornium.Schema.Faction.strip_old_members(members, faction_id)
    Tornium.Schema.FactionPosition.remove_old_positions(positions, faction_id)

    :ok
  end

  defp do_perform(api_call_result, faction_id, false = _nonpublic?)
       when is_map(api_call_result) and is_integer(faction_id) do
    %{
      Torngen.Client.Path.Faction.Id.Basic => %{
        FactionBasicResponse => %Torngen.Client.Schema.FactionBasicResponse{basic: basic_data}
      },
      Torngen.Client.Path.Faction.Id.Members => %{
        FactionMembersResponse => %Torngen.Client.Schema.FactionMembersResponse{members: members_data}
      }
    } =
      Tornex.SpecQuery.new()
      |> Tornex.SpecQuery.put_path(Torngen.Client.Path.Faction.Id.Basic)
      |> Tornex.SpecQuery.put_path(Torngen.Client.Path.Faction.Id.Members)
      |> Tornex.SpecQuery.parse(api_call_result)

    Tornium.Schema.Faction.upsert(basic_data)

    positions =
      Tornium.Schema.FactionPosition
      |> where([p], p.faction_id == ^faction_id)
      |> Repo.all()

    members_data
    |> Tornium.Schema.Faction.upsert_members(positions, faction_id)
    |> Tornium.Schema.Faction.strip_old_members(faction_id)

    :ok
  end
end
