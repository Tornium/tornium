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

defmodule Tornium.Workers.OCUpdate do
  alias Tornium.Repo
  import Ecto.Query

  use Oban.Worker,
    max_attempts: 3,
    priority: 0,
    queue: :faction_processing,
    tags: ["faction", "oc"],
    unique: [
      period: :infinity,
      fields: [:worker, :args],
      keys: [:faction_tid],
      states: :incomplete
    ]

  @impl Oban.Worker
  def perform(
        %Oban.Job{
          args: %{
            "api_call_id" => api_call_id,
            "faction_id" => faction_id,
            "user_id" => user_id
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
        |> where([u], u.tid == ^user_id and u.faction_id == ^faction_id)
        |> Repo.update_all([])

        :ok

      %{"error" => %{"code" => error_code}} when is_integer(error_code) ->
        {:cancel, {:api_error, error_code}}

      %{"crimes" => crime_data} when is_map(crime_data) ->
        # When an OC's crime response is a map instead of a list, this indicates that the
        # faction is still on OCs 1.0 and hasn't migrated. We should force update the 
        # migration flag for this faction to indicate this as this worker shouldn't be
        # running for factions that haven't migrated yet.

        Tornium.Schema.Faction
        |> update([f], set: [has_migrated_oc: false])
        |> where([f], f.tid == ^faction_id)
        |> Repo.update_all([])

        :ok

      result when is_map(result) ->
        do_perform(result)
    end
  end

  @doc false
  @spec do_perform(api_call_result :: map()) :: Oban.Worker.result()
  def do_perform(api_call_result) when is_map(api_call_result) do
    %{
      Torngen.Client.Path.Faction.Basic => %{
        FactionBasicResponse => %Torngen.Client.Schema.FactionBasicResponse{
          basic: %Torngen.Client.Schema.FactionBasic{id: faction_id} = _basic_data
        }
      },
      Torngen.Client.Path.Faction.Members => %{
        FactionMembersResponse => %Torngen.Client.Schema.FactionMembersResponse{members: members_data}
      },
      Torngen.Client.Path.Faction.Crimes => %{
        FactionCrimesResponse => %Torngen.Client.Schema.FactionCrimesResponse{crimes: crimes_data}
      }
    } =
      0
      |> Tornium.Workers.OCUpdateScheduler.query()
      |> Tornex.SpecQuery.parse(api_call_result)

    config = Tornium.Schema.ServerOCConfig.get_by_faction(faction_id)
    parsed_crimes = Tornium.Faction.OC.parse(crimes_data, members_data, faction_id)

    # `Repo.preload` is required to load additional information for performing and rending the checks
    check_state =
      parsed_crimes
      |> Tornium.Schema.OrganizedCrime.upsert_all()
      |> Repo.preload(slots: [:item_required, :user, oc: [:faction]])
      |> Tornium.Faction.OC.check(config)

    parsed_crimes
    |> Enum.flat_map(fn %Tornium.Schema.OrganizedCrime{oc_name: oc_name, slots: slots} ->
      Enum.map(slots, fn
        %Tornium.Schema.OrganizedCrimeSlot{user_id: nil} ->
          nil

        %Tornium.Schema.OrganizedCrimeSlot{
          user_id: user_id,
          crime_position: crime_position,
          user_success_chance: cpr,
          user_joined_at: user_joined_at
        } ->
          %Tornium.Schema.OrganizedCrimeCPR{
            guid: Ecto.UUID.generate(),
            user_id: user_id,
            oc_name: oc_name,
            oc_position: crime_position,
            cpr: cpr,
            updated_at: user_joined_at
          }
      end)
    end)
    |> Enum.reject(&is_nil/1)
    |> Enum.reverse()
    |> Enum.uniq_by(fn %Tornium.Schema.OrganizedCrimeCPR{user_id: user_id, oc_name: oc_name, oc_position: oc_position} ->
      {user_id, oc_name, oc_position}
    end)
    |> Tornium.Schema.OrganizedCrimeCPR.upsert_all()

    check_state
    |> Tornium.Faction.OC.Render.render_all(config)
    |> Tornium.Discord.send_messages()

    # Perform this after the attempting to send the messages to avoid a flag being updated despite the message not being sent (e.g. from a rendering issue)
    Tornium.Schema.OrganizedCrimeSlot.update_sent_state(check_state)

    :ok
  end

  @impl Oban.Worker
  def timeout(%Oban.Job{} = _job) do
    :timer.minutes(1)
  end
end
