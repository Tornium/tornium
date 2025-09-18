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

defmodule Tornium.Workers.OverdoseUpdate do
  @moduledoc """
  Insert events for new overdoses and send notifications for those overdoses.

  1. Insert all members into the DB with overdose count of 0 (ignoring conflicts) to ensure there's an existing value to update from.
  2. Update all members' overdose counts. Returns the rows updated while skipping newly inserted members.
  3. Insert the members with updated counts into the overdose events.
  4. Send overdose notifications to the linked server if configured.
  """

  alias Torngen.Client.Schema.FactionContributor
  alias Torngen.Client.Schema.FactionContributorsResponse
  alias Tornium.Repo
  import Ecto.Query

  use Oban.Worker,
    max_attempts: 3,
    priority: 0,
    queue: :faction_processing,
    tags: ["faction"],
    unique: [
      period: :infinity,
      fields: [:worker, :args],
      keys: [:api_call_id],
      states: :incomplete
    ]

  @impl Oban.Worker
  def perform(
        %Oban.Job{
          args: %{
            "api_call_id" => api_call_id,
            "faction_id" => faction_id
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

      %{} = result ->
        %{
          Torngen.Client.Path.Faction.Contributors => %{
            FactionContributorsResponse => %FactionContributorsResponse{contributors: overdose_data}
          }
        } =
          Tornex.SpecQuery.new()
          |> Tornex.SpecQuery.put_path(Torngen.Client.Path.Faction.Contributors)
          |> Tornex.SpecQuery.put_parameter(:stat, "drugoverdoses")
          |> Tornex.SpecQuery.put_parameter(:cat, "current")
          |> Tornex.SpecQuery.parse(result)

        {_, new_members} =
          Repo.insert_all(
            Tornium.Schema.OverdoseCount,
            Tornium.Faction.Overdose.map_new_counts(overdose_data, faction_id),
            on_conflict: :nothing,
            conflict_target: [:faction_id, :user_id],
            returning: [:user_id]
          )

        new_member_ids = Enum.map(new_members, fn %Tornium.Schema.OverdoseCount{user_id: member_id} -> member_id end)

        {_, overdosed_members} =
          Repo.insert_all(
            Tornium.Schema.OverdoseCount,
            Tornium.Faction.Overdose.map_counts(overdose_data, faction_id),
            on_conflict: {:replace, [:count, :updated_at]},
            conflict_target: [:user_id, :faction_id],
            returning: [:user_id]
          )

        {_, overdose_events} =
          Repo.insert_all(
            Tornium.Schema.OverdoseEvents,
            Tornium.Faction.Overdose.map_events(overdosed_members, faction_id, new_member_ids),
            returning: true
          )

        send_notifications(overdose_events, faction_id)

        :ok
    end
  end

  defp send_notifications([] = _overdose_events, faction_id) when is_integer(faction_id) do
    nil
  end

  defp send_notifications(overdose_events, faction_id) when is_list(overdose_events) and is_integer(faction_id) do
    faction_id
    |> Tornium.Schema.ServerOverdoseConfig.get_by_faction()
    |> do_send_notifications(overdose_events)
  end

  defp do_send_notifications(
         %Tornium.Schema.ServerOverdoseConfig{policy: :immediate, channel: channel},
         overdose_events
       )
       when is_integer(channel) and channel != 0 and is_list(overdose_events) do
    overdose_events
    |> Repo.preload(:faction)
    |> Repo.preload(:user)
    |> Enum.map(&Tornium.Faction.Overdose.to_embed/1)
    |> Tornium.Discord.chunk_embeds(chunk_size: 10)
    |> Tornium.Discord.send_messages()

    Tornium.Schema.OverdoseEvent.notify_all(overdose_events)
  end

  defp do_send_notifications(_server_overdose_config, overdose_events) when is_list(overdose_events) do
    # No notifications will be sent as the following are true:
    #   - Server OD config has not been created
    #   - Server OD channel has not been set up
    #   - Faction is not linked to a server
    nil
  end

  @impl Oban.Worker
  def timeout(%Oban.Job{} = _job) do
    :timer.minutes(3)
  end
end
