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
  require Logger
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
            "api_key" => api_key,
            "user_tid" => user_tid,
            "faction_tid" => faction_tid
          }
        } = _job
      ) do
    config = Tornium.Schema.ServerOCConfig.get_by_faction(faction_tid)

    parsed_crimes =
      %Tornex.Query{
        resource: "v2/faction",
        resource_id: faction_tid,
        key: api_key,
        selections: ["crimes", "members"],
        key_owner: user_tid,
        nice: 10
      }
      |> Tornex.Scheduler.Bucket.enqueue()
      |> Tornium.Faction.OC.parse(faction_tid)

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

    # This should be performed after Workers.OCUpdate is run to ensure the OCs have been updated/inserted to the database.
    # Only factions with at least one OC team should perform this update
    count =
      Tornium.Schema.OrganizedCrimeTeam
      |> where([t], t.faction_id == ^faction_tid)
      |> select(count())
      |> Repo.one()

    case count do
      _ when count >= 1 ->
        %{faction_tid: faction_tid}
        |> Tornium.Workers.OCTeamUpdate.new()
        |> Oban.insert()

      _ ->
        nil
    end

    :ok
  end

  @impl Oban.Worker
  def timeout(%Oban.Job{} = _job) do
    :timer.minutes(3)
  end
end
