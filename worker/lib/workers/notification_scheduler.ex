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

defmodule Tornium.Workers.NotificationScheduler do
  require Logger
  alias Tornium.Repo
  import Ecto.Query

  use Oban.Worker,
    max_attempts: 5,
    priority: 0,
    queue: :scheduler,
    tags: ["scheduler", "notification"],
    unique: [
      period: :infinity,
      fields: [:worker],
      states: :incomplete
    ]

  @impl Oban.Worker
  def perform(%Oban.Job{} = _job) do
    Logger.debug("Scheduling notifications")
    now = DateTime.utc_now()

    # Schedule notifications for Discord servers where notifications are enabled
    # TODO: Determine how this can be modified into query to include notifications outside of Discord servers
    Tornium.Schema.Notification
    |> where([n], not is_nil(n.server_id))
    |> where([n], n.enabled == true)
    |> join(:inner, [n], t in assoc(n, :trigger))
    |> where([n, t, s, c], t.next_execution <= ^now or is_nil(t.next_execution))
    |> join(:inner, [n, t], s in assoc(n, :server))
    |> join(:inner, [n, t, s], c in assoc(s, :notifications_config))
    |> where([n, t, s, c], c.enabled == true)
    |> preload([n, t, s, c], trigger: t)
    |> Repo.all()
    |> Enum.group_by(&{&1.trigger.resource, &1.resource_id})
    |> Enum.each(fn {{resource, resource_id}, notifications} ->
      %{
        resource_id: resource_id,
        resource: resource,
        notifications: Enum.map(notifications, fn notification -> notification.nid end)
      }
      |> Tornium.Workers.Notification.new()
      |> Oban.insert()
    end)

    :ok
  end
end
