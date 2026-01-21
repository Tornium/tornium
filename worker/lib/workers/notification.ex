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

defmodule Tornium.Workers.Notification do
  require Logger
  alias Tornium.Repo
  import Ecto.Query

  use Oban.Worker,
    max_attempts: 3,
    priority: 5,
    queue: :notifications,
    tags: ["notification"],
    unique: [
      period: :infinity,
      fields: [:worker, :args],
      keys: [:resource, :resource_id, :restricted],
      states: :incomplete
    ]

  @impl Oban.Worker
  def perform(
        %Oban.Job{
          args: %{
            "notifications" => notifications_ids,
            "resource" => resource,
            "resource_id" => resource_id,
            "restricted" => _restricted?,
            "api_call_id" => api_call_id
          }
        } = _job
      ) do
    api_call_id
    |> Tornium.API.Store.pop()
    |> do_perform(notifications_ids, resource, resource_id)
  end

  @spec do_perform(
          response :: map() | :not_ready | :expired | nil,
          notifications_ids :: [String.t()],
          resource :: String.t(),
          resource_id :: integer()
        ) :: Oban.Worker.result()
  defp do_perform(response, notifications_ids, _resource, _resource_id)
       when is_nil(response) and is_list(notifications_ids) do
    # When a notification is cancelled because of an invalid call ID, we still want to update the next execution to ensure that
    # the notification is run again within an appropriate timeframe.

    notifications =
      Tornium.Schema.Notification
      |> where([n], n.nid in ^notifications_ids)
      |> join(:inner, [n], t in assoc(n, :trigger), on: t.tid == n.trigger_id)
      |> preload([n, t, s], trigger: t)
      |> Repo.all()

    notifications
    |> Enum.uniq_by(fn %Tornium.Schema.Notification{} = notification -> notification.trigger end)
    |> Enum.each(fn %Tornium.Schema.Notification{trigger: %Tornium.Schema.Trigger{} = trigger} ->
      Tornium.Notification.update_next_execution(trigger)
    end)

    {:cancel, :invalid_call_id}
  end

  defp do_perform(:expired = _response, notifications_ids, _resource, _resource_id) when is_list(notifications_ids) do
    # When a notification is cancelled because of an expired API call result, we still want to update the next
    # execution to ensure that the notification is run again within an appropriate timeframe.

    notifications =
      Tornium.Schema.Notification
      |> where([n], n.nid in ^notifications_ids)
      |> join(:inner, [n], t in assoc(n, :trigger), on: t.tid == n.trigger_id)
      |> preload([n, t, s], trigger: t)
      |> Repo.all()

    notifications
    |> Enum.uniq_by(fn %Tornium.Schema.Notification{} = notification -> notification.trigger end)
    |> Enum.each(fn %Tornium.Schema.Notification{trigger: %Tornium.Schema.Trigger{} = trigger} ->
      Tornium.Notification.update_next_execution(trigger)
    end)

    {:cancel, :expired}
  end

  defp do_perform(:not_ready = _response, _notification_ids, _resource, _resource_id) do
    {:error, :not_ready}
  end

  defp do_perform(%{"error" => %{"code" => error_code}} = _response, _notifications_ids, _resource, _resource_id)
       when error_code in [] do
    # This handles error codes that need to be handled in a specific manner. Generic Torn API errors can be handled by
    # cancelling or erroring the job.

    # TODO: Implement this
  end

  defp do_perform(%{"error" => %{"code" => error_code}} = _response, _notifications_ids, _resource, _resource_id)
       when is_integer(error_code) do
    # TODO: Implement this
  end

  defp do_perform(response, notifications_ids, resource, _resource_id)
       when is_map(response) and is_list(notifications_ids) do
    notifications =
      Tornium.Schema.Notification
      |> where([n], n.nid in ^notifications_ids)
      |> join(:inner, [n], t in assoc(n, :trigger), on: t.tid == n.trigger_id)
      |> join(:inner, [n, t], s in assoc(n, :server), on: s.sid == n.server_id)
      |> preload([n, t, s], trigger: t, server: s)
      |> Repo.all()

    notifications
    |> Enum.uniq_by(fn %Tornium.Schema.Notification{} = notification -> notification.trigger end)
    |> Enum.each(fn %Tornium.Schema.Notification{trigger: %Tornium.Schema.Trigger{} = trigger} ->
      Tornium.Notification.update_next_execution(trigger)
    end)

    resource = String.to_atom(resource)

    notifications
    |> Enum.group_by(& &1.trigger_id)
    |> Enum.each(fn {_trigger_id, [%Tornium.Schema.Notification{trigger: trigger} | _] = trigger_notifications} ->
      response
      |> Tornium.Notification.filter_response(resource, trigger.selections)
      |> Tornium.Notification.handle_api_response(trigger, trigger_notifications)
    end)
  end

  @impl Oban.Worker
  def timeout(_job) do
    :timer.seconds(30)
  end
end
