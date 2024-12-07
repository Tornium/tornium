# Copyright (C) 2021-2023 tiksan
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
    unique: [period: 45]

  @impl Oban.Worker
  def perform(%Oban.Job{} = _job) do
    Logger.debug("Scheduling notifications")

    Tornium.Schema.Notification
    |> join(:inner, [n], t in assoc(n, :trigger), on: t.tid == n.trigger_id)
    |> preload([n, t], trigger: t)
    |> Repo.all()
    |> Enum.group_by(&{&1.trigger.resource, &1.resource_id})
    |> Enum.map(fn {{resource, resource_id}, notifications} ->
      %{
        resource_id: resource_id,
        resource: resource,
        notifications: Enum.map(notifications, fn notification -> notification.nid end)
      }
      |> Tornium.Workers.Notification.new()
      |> Oban.insert()
    end)
    |> IO.inspect()

    :ok
  end
end
