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

defmodule Tornium.Notification do
  alias Tornium.Repo
  import Ecto.Query

  @api_call_priority 10

  @type trigger_return() :: {:ok, list(any())} | {:error, any()} | {:lua_error, any()}

  @spec execute_resource(
          resource :: atom(),
          resource_id :: integer(),
          notifications :: list(Tornium.Schema.Notification.t())
        ) :: list(trigger_return())
  def execute_resource(_resource = :user, resource_id, notifications) when is_list(notifications) do
    {selections, users} =
      Enum.reduce(notifications, {MapSet.new([]), []}, fn notification, {s, u} ->
        {
          MapSet.union(s, MapSet.new(notification.trigger.selections)),
          [u | notification.user_id]
        }
      end)

    api_key =
      Tornium.Schema.TornKey
      |> where([k], k.user_id in ^users)
      |> select([:api_key, :user_id])
      |> order_by(fragment("RANDOM()"))
      |> Repo.one!()

    response =
      Tornex.Scheduler.Bucket.enqueue(
        resource: "user",
        resource_id: resource_id,
        selections: selections,
        key: api_key.api_key,
        key_owner: api_key.user_id,
        nice: @api_call_priority
      )

    return_value = Enum.map(notifications, fn notification -> handle_response(response, notification) end)
    return_value
  end

  @spec execute(notification :: Tornium.Schema.Notification.t(), api_key :: Tornium.Schema.TornKey.t()) ::
          trigger_return()
  def execute(
        %Tornium.Schema.Notification{trigger: %Tornium.Schema.Trigger{resource: :user}} = notification,
        %Tornium.Schema.TornKey{} = api_key
      ) do
    # TODO: Document this function
    update_next_execution(notification)

    Tornex.Scheduler.Bucket.enqueue(%Tornex.Query{
      resource: "user",
      resource_id: notification.resource_id,
      selections: notification.trigger.selections,
      key: api_key.api_key,
      key_owner: api_key.user_id,
      nice: @api_call_priority
    })
    |> handle_response(notification)
  end

  # TODO: Handle spec response type
  @spec handle_response(response :: map(), notification :: Tornium.Schema.Notification.t()) :: trigger_return()
  defp handle_response(
         %{"error" => %{"code" => code, "error" => error}} = _response,
         %Tornium.Schema.Notification{} = _notification
       ) do
    {:error, Tornium.API.Error.construct(code, error)}
  end

  defp handle_response(%{} = response, notification) do
    # TODO: Handle errors from `Tornium.Lua.execute_lua`
    Tornium.Lua.execute_lua(notification.trigger.code, user: response)
  end

  @spec parse_next_execution(notification :: Tornium.Schema.Notification.t()) :: DateTime.t()
  defp parse_next_execution(%Tornium.Schema.Notification{} = notification) do
    # TODO: Document this function
    Crontab.CronExpression.Parser.parse!(notification.cron)
    |> Crontab.Scheduler.get_next_run_date!()
    |> DateTime.from_naive!("Etc/UTC")
  end

  @spec update_next_execution(notification :: Tornium.Schema.Notification.t()) :: nil
  def update_next_execution(%Tornium.Schema.Notification{} = notification) do
    # TODO: Document this function
    {1, _} =
      Tornium.Schema.Notification
      |> where(nid: ^notification.nid)
      |> update(set: [next_execution: ^parse_next_execution(notification)])
      |> Repo.update_all([])

    nil
  end
end
