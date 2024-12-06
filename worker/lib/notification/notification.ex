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
  @type trigger_resource() :: :user | :faction

  @doc """
  Execute all notifications against a specific resource (e.g. a certain user ID) with a single API call to retrieve the union.
  """
  @spec execute_resource(
          resource :: trigger_return(),
          resource_id :: integer(),
          notifications :: [Tornium.Schema.Notification.t()]
        ) :: [trigger_return()]
  def execute_resource(resource, resource_id, notifications) when is_list(notifications) do
    # Determine the union of selections and users for all notifications against a specific resource and resource ID
    {selections, users} =
      Enum.reduce(notifications, {MapSet.new([]), MapSet.new([])}, fn notification, {s, u} ->
        # Use the IDs of admins when the notification is for a Discord server as to avoid issues with missing API keys

        case notification.server do
          nil ->
            {
              # NOTE: This chunk of the codebase is not implemented yet
              MapSet.union(s, MapSet.new(notification.trigger.selections)),
              MapSet.put(u, notification.user_id)
            }

          guild ->
            {
              MapSet.union(s, MapSet.new(notification.trigger.selections)),
              MapSet.union(u, MapSet.new(guild.admins))
            }
        end
      end)

    api_key =
      Tornium.Schema.TornKey
      |> where([k], k.user_id in ^users)
      |> select([:api_key, :user_id])
      |> order_by(fragment("RANDOM()"))
      |> Repo.one()

    case api_key do
      nil ->
        # TODO: Disable the notifications and push updates to audit log channels
        nil

      %Tornium.Schema.TornKey{} ->
        response = resource_data(resource, resource_id, selections, api_key)

        notifications
        |> Enum.group_by(& &1.trigger)
        |> Enum.map(fn {%Tornium.Schema.Trigger{} = trigger, trigger_notifications} ->
          response
          |> filter_response(trigger.resource, trigger.selections)
          |> handle_response(trigger_notifications)
        end)
    end
  end

  @spec resource_data(
          resource :: trigger_resource(),
          resource_id :: integer(),
          selections :: [String.t()],
          api_key :: Tornium.Schema.TornKey.t()
        ) :: map()
  defp resource_data(:user, resource_id, selections, api_key) do
    Tornex.Scheduler.Bucket.enqueue(
      resource: "user",
      resource_id: resource_id,
      selections: selections,
      key: api_key.api_key,
      key_owner: api_key.user_id,
      nice: @api_call_priority
    )
  end

  defp resource_data(:faction, resource_id, selections, api_key) do
    Tornex.Scheduler.Bucket.enqueue(
      resource: "faction",
      resource_id: resource_id,
      selections: selections,
      key: api_key.api_key,
      key_owner: api_key.user_id,
      nice: @api_call_priority
    )
  end

  @doc """
  Filter the API response to only the keys required for the trigger's selection(s).
  """
  @spec filter_response(
          response :: map(),
          resource :: Tornium.Notification.trigger_resource(),
          selections :: [String.t()]
        ) :: map()
  def filter_response(response, resource, selections) when is_list(selections) do
    valid_keys =
      Enum.reduce(selections, MapSet.new([]), fn selection, acc ->
        MapSet.union(acc, MapSet.new(Tornium.Notification.Selections.get_selection_keys(resource, selection)))
      end)

    Map.filter(response, fn {key, _value} -> Enum.member?(valid_keys, key) end)
  end

  # TODO: Handle spec response type
  @spec handle_response(response :: map(), notifications :: [Tornium.Schema.Notification.t()]) :: trigger_return()
  defp handle_response(
         %{"error" => %{"code" => code, "error" => error}} = _response,
         notifications
       )
       when is_list(notifications) do
    {:error, Tornium.API.Error.construct(code, error)}
  end

  defp handle_response(%{} = response, notifications) when is_list(notifications) do
    # TODO: Handle errors from `Tornium.Lua.execute_lua`
    Tornium.Lua.execute_lua(Enum.at(notifications, 0).trigger.code, user: response)
    |> IO.inspect()
  end

  @spec parse_next_execution(notification :: Tornium.Schema.Notification.t()) :: DateTime.t()
  defp parse_next_execution(%Tornium.Schema.Notification{} = notification) do
    # TODO: Document this function
    Crontab.CronExpression.Parser.parse!(notification.trigger.cron)
    |> Crontab.Scheduler.get_next_run_date!()
    |> DateTime.from_naive!("Etc/UTC")
  end

  @spec update_next_execution(notification :: Tornium.Schema.Notification.t()) :: nil
  defp update_next_execution(%Tornium.Schema.Notification{} = notification) do
    # TODO: Document this function
    {1, _} =
      Tornium.Schema.Notification
      |> where(nid: ^notification.nid)
      |> update(set: [next_execution: ^parse_next_execution(notification)])
      |> Repo.update_all([])

    nil
  end
end
