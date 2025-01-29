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

defmodule Tornium.Workers.Notification do
  require Logger
  alias Tornium.Repo
  import Ecto.Query

  use Oban.Worker,
    max_attempts: 2,
    priority: 5,
    queue: :notifications,
    tags: ["notification"]

  # TODO: Make each resource + resource_id unique for the same 45 seconds as the secheduler

  @impl Oban.Worker
  def perform(
        %Oban.Job{args: %{"notifications" => notifications_ids, "resource" => resource, "resource_id" => resource_id}} =
          _job
      ) do
    notifications =
      Tornium.Schema.Notification
      |> where([n], n.nid in ^notifications_ids)
      |> join(:inner, [n], t in assoc(n, :trigger), on: t.tid == n.trigger_id)
      |> join(:inner, [n, t], s in assoc(n, :server), on: s.sid == n.server_id)
      |> preload([n, t, s], trigger: t, server: s)
      |> Repo.all()

    notifications
    |> Enum.uniq_by(fn %Tornium.Schema.Notification{} = notification -> notification.trigger end)
    |> Enum.map(fn %Tornium.Schema.Notification{trigger: %Tornium.Schema.Trigger{} = trigger} = _notification ->
      Tornium.Notification.update_next_execution(trigger)
    end)

    Tornium.Notification.execute_resource(String.to_atom(resource), resource_id, notifications)

    :ok
  end
end
