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
  @moduledoc """
  Worker to group and enqueue similar notifications as seperate tasks.

  If the notification is set up to work within a Discord server, the server will need to have a
  channel ID and a notification configuration and the server's notification configuration must 
  be enabled. If the notification is not set up to run within a Discord server, the notification
  will be served through the gateway and...
  """

  # TODO: Add conditions for serving the notification through the gateway

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
    now = DateTime.utc_now()

    Tornium.Schema.Notification
    |> where([n], n.enabled == true)
    |> join(:inner, [n], t in assoc(n, :trigger))
    |> where([n, t, s, c], t.next_execution <= ^now or is_nil(t.next_execution))
    |> join(:left, [n, t], s in assoc(n, :server))
    |> join(:left, [n, t, s], c in assoc(s, :notifications_config))
    |> where(
      [n, t, s, c],
      (not is_nil(n.server_id) and not is_nil(s.notifications_config_id) and c.enabled == true and
         not is_nil(n.channel_id)) or is_nil(n.server_id)
    )
    |> preload([n, t, s, c], trigger: t)
    |> Repo.all()
    |> Enum.group_by(&{&1.trigger.resource, &1.resource_id})
    |> Enum.each(fn {{resource, resource_id}, notifications} ->
      # To be cautious, notifications are split by whether they utilize restricted data. Notifications that
      # do will be executed as an owner of the resource. All other notifications will be executed as a 
      # random server admin/user using the notification. This will prevent the leakage of data in the API
      # call that may change for API endpoints with changing responses depending on the caller being a
      # resource owner.

      notifications
      |> Enum.group_by(fn notification -> notification.trigger.restricted_data end)
      |> Enum.each(fn {restricted?, grouped_notifications} ->
        start_notifications(resource, resource_id, restricted?, grouped_notifications)
      end)
    end)

    :ok
  end

  @doc """
  Start the notifications for a specific resource + resource ID in the Tornex task supervisor and 
  handoff the processing of the notification to the `Tornium.Workers.Notification` worker.
  """
  @spec start_notifications(
          resource :: Tornium.Notification.trigger_resource(),
          resource_id :: integer(),
          restricted? :: boolean(),
          notifications :: [Tornium.Schema.Notification.t()]
        ) :: term()
  def start_notifications(_resource, _resource_id, _restricted?, [] = _notifications) do
    nil
  end

  def start_notifications(resource, resource_id, restricted?, notifications) when is_binary(resource) do
    api_key = Tornium.Notification.get_api_key(resource, resource_id, restricted?, notifications)

    case api_key do
      %Tornium.Schema.TornKey{} ->
        query =
          Tornium.Notification.to_query(
            resource,
            resource_id,
            Tornium.Notification.get_selections(notifications),
            api_key
          )

        api_call_id = Ecto.UUID.generate()
        Tornium.API.Store.create(api_call_id, 300)

        Task.Supervisor.async_nolink(Tornium.TornexTaskSupervisor, fn ->
          query
          |> Tornex.Scheduler.Bucket.enqueue()
          |> Tornium.API.Store.insert(api_call_id)
        end)

        %{
          resource_id: resource_id,
          resource: resource,
          restricted: restricted?,
          notifications: Enum.map(notifications, & &1.nid),
          # TODO: Consider adding this later for improved debugging
          # origin_job_id: job_id,
          api_call_id: api_call_id
        }
        |> Tornium.Workers.Notification.new(schedule_in: _seconds = 15)
        |> Oban.insert()

      nil ->
        # All notifications in this group need to be disabled at this stage instead of specific
        # notifications given the overall lack of API keys across all the notifications.

        Enum.each(notifications, fn %Tornium.Schema.Notification{} = notification ->
          Tornium.Notification.Audit.log(:no_api_keys, notification)
        end)

        Tornium.Schema.Notification.disable(notifications, "No API keys to use")

      :skip ->
        # This case occurs when there is an API key available but certain notifications had to be
        # disabled in `Tornium.Notification.get_api_key/4` due to some permission-related issue with
        # a restricted notification.

        nil
    end
  end
end
