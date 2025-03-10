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

  use Oban.Worker,
    max_attempts: 3,
    priority: 0,
    queue: :faction_processing,
    tags: ["faction", "oc"],
    # TODO: Update unique period
    unique: [period: 45]

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
    request = %Tornex.Query{
      resource: "v2/faction",
      resource_id: faction_tid,
      key: api_key,
      selections: ["crimes", "members"],
      key_owner: user_tid,
      nice: 10
    }

    check_state =
      request
      |> Tornex.Scheduler.Bucket.enqueue()
      |> Tornium.Faction.OC.parse(faction_tid)
      |> Tornium.Schema.OrganizedCrime.upsert_all()
      |> Repo.preload(slots: [:oc, :item_required, user: [:faction]])
      # Required for rending the checks
      # TODO: Preload after checks to reduce DB load
      |> Tornium.Faction.OC.check()

    check_state
    |> Tornium.Faction.OC.Render.render_all(faction_tid)
    |> Tornium.Discord.send_messages(collect: false)

    # Perform this after the attempting to send the messages to avoid a flag being updated despite the message not being sent (e.g. from a rendering issue)
    # TODO: Only update this if the config is enabled for the feature
    Tornium.Schema.OrganizedCrimeSlot.update_sent_state(check_state)

    :ok
  end
end
