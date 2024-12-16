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
  require Logger
  alias Tornium.Repo
  import Ecto.Query

  @api_call_priority 10

  @type trigger_resource() :: :user | :faction

  @doc """
  Execute all notifications against a specific resource (e.g. a certain user ID) with a single API call to retrieve the union.
  """
  @spec execute_resource(
          resource :: trigger_resource(),
          resource_id :: integer(),
          notifications :: [Tornium.Schema.Notification.t()]
        ) :: [Tornium.Lua.trigger_return()]
  def execute_resource(resource, resource_id, notifications) when is_list(notifications) do
    # Determine the union of selections and users for all notifications against a specific resource and resource ID
    {selections, users} =
      Enum.reduce(notifications, {MapSet.new([]), MapSet.new([])}, fn notification, {s, u} ->
        # Use the IDs of admins when the notification is for a Discord server as to avoid issues with missing API keys

        case notification.server do
          nil ->
            # Use this when the notification is not for a server and is intended to be sent through the SSE gateway
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
      |> where([k], k.user_id in ^MapSet.to_list(users))
      |> select([:api_key, :user_id])
      |> order_by(fragment("RANDOM()"))
      |> Repo.one()

    case api_key do
      nil ->
        # TODO: Disable the notifications and push updates to audit log channels
        Logger.info("no API key")
        nil

      %Tornium.Schema.TornKey{} ->
        IO.inspect(resource)
        response = resource_data(resource, resource_id, selections, api_key)

        notifications
        |> Enum.group_by(& &1.trigger)
        |> Enum.map(fn {%Tornium.Schema.Trigger{} = trigger, trigger_notifications} ->
          response
          |> filter_response(trigger.resource, trigger.selections)
          |> handle_response(trigger, trigger_notifications)
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
    Tornex.Scheduler.Bucket.enqueue(%Tornex.Query{
      resource: "user",
      resource_id: resource_id,
      selections: selections,
      key: api_key.api_key,
      key_owner: api_key.user_id,
      nice: @api_call_priority
    })
  end

  defp resource_data(:faction, resource_id, selections, api_key) do
    Tornex.Scheduler.Bucket.enqueue(%Tornex.Query{
      resource: "faction",
      resource_id: resource_id,
      selections: selections,
      key: api_key.api_key,
      key_owner: api_key.user_id,
      nice: @api_call_priority
    })
  end

  @doc """
  Filter the API response to only the keys required for the trigger's selection(s).
  """
  @spec filter_response(
          response :: map(),
          resource :: trigger_resource(),
          selections :: [String.t()]
        ) :: map()
  def filter_response(response, resource, selections) when is_list(selections) do
    valid_keys =
      Enum.reduce(selections, MapSet.new([]), fn selection, acc ->
        MapSet.union(acc, MapSet.new(Tornium.Notification.Selections.get_selection_keys(resource, selection)))
      end)

    Map.filter(response, fn {key, _value} -> Enum.member?(valid_keys, key) end)
  end

  @spec handle_response(
          response :: map(),
          trigger :: Tornium.Schema.Trigger.t(),
          notifications :: [Tornium.Schema.Notification.t()]
        ) :: any()
  defp handle_response(
         # TODO: Update typespec for this
         %{"error" => %{"code" => code, "error" => error}} = _response,
         _trigger,
         _notifications
       ) do
    {:error, Tornium.API.Error.construct(code, error)}
  end

  defp handle_response(%{} = response, trigger, notifications) when is_list(notifications) do
    Enum.map(notifications, fn %Tornium.Schema.Notification{} = notification ->
      Tornium.Lua.execute_lua(trigger.code, generate_lua_state_map(notification, response))
      |> handle_lua_execution(notification)
    end)
  end

  @doc """
  Handle the returned states (or errors) from the Lua trigger code. If successfully executed, the states will be used
  to create the message to be sent/updated. If there's an error from the Lua code, the notification will be disabled.
  """
  @spec handle_lua_execution(Tornium.Lua.trigger_return(), notification :: Tornium.Schema.Notification.t()) :: nil
  defp handle_lua_execution(
         {:ok, [triggered?: true, render_state: %{} = render_state, passthrough_state: %{} = passthrough_state]},
         %Tornium.Schema.Notification{
           trigger: %Tornium.Schema.Trigger{message_template: trigger_message_template, message_type: :update}
         } = notification
       ) do
    render_message(trigger_message_template, render_state)
    |> validate_message()
    |> IO.inspect()
    |> try_message(:update, notification)
    |> IO.inspect()

    # TODO: Update passthrough state
  end

  defp handle_lua_execution(
         {:ok, [triggered?: true, render_state: %{} = render_state, passthrough_state: %{} = passthrough_state]},
         %Tornium.Schema.Notification{
           trigger: %Tornium.Schema.Trigger{message_template: trigger_message_template, message_type: :send}
         } = notification
       ) do
    render_message(trigger_message_template, render_state)
    |> validate_message()
    |> try_message(:send, notification)
    |> IO.inspect()

    # TODO: Update passthrough state
  end

  defp handle_lua_execution(
         {:ok, [triggered?: false, render_state: %{} = _render_state, passthrough_state: %{} = passthrough_state]},
         %Tornium.Schema.Notification{} = _notification
       ) do
    # TODO: Update passthrough state
  end

  defp handle_lua_execution({:lua_error, error}, %Tornium.Schema.Notification{} = notification) do
    # TODO: Update database with error and to disable notification
    # TODO: Send message to audit log channel if applicable
  end

  defp handle_lua_execution({:error, %Tornium.API.Error{} = torn_error}, %Tornium.Schema.Notification{} = notification) do
    # TODO: Handle this error
  end

  defp handle_lua_execution({:error, reason}, %Tornium.Schema.Notification{} = notification) do
    IO.inspect(reason)
    # TODO: Handle this error
    {:error, reason}
  end

  defp handle_lua_execution(trigger_return, notification) do
    # Invalid response
    IO.inspect(trigger_return)
    IO.inspect(notification)
    throw(Exception)
  end

  @spec render_message(template :: String.t(), state :: map()) :: String.t() | nil
  defp render_message(template, %{} = state) do
    # Attempt to render the JSON message for a notification provided the render state and the Solid template.
    # TODO: Improve the error handling upon errors from Solid

    try do
      template
      |> Solid.parse!()
      |> Solid.render!(state)
      |> Kernel.to_string()
      |> String.replace(["\n", "\t"], "")
      |> IO.inspect()
    rescue
      e ->
        IO.inspect(e)
        # TODO: Handle error
        nil
    end
  end

  @spec validate_message(message :: String.t()) :: map() | nil
  defp validate_message(message) when is_nil(message) do
    nil
  end

  defp validate_message(message) do
    # Validate the rendered JSON Discord message to avoid unnecessary Discord API calls.

    case Jason.decode(message) do
      {:ok, parsed_message} ->
        parsed_message

      {:error, reason} ->
        IO.inspect(reason)
        nil
    end
  end

  @doc """
  Attempt to send or update a message for a notification depending on the notification's configuration
  """
  @spec try_message(
          message :: map() | nil,
          action_type :: :send | :update,
          notification :: Tornium.Schema.Notification.t()
        ) ::
          {:ok, Nostrum.Struct.Message.t()} | {:error, Nostrum.Error.ApiError.t()} | {:error, :unknown} | nil
  defp try_message(message, _action_type, _notification) when is_nil(message) do
    # There is no message to act upon. This should just act as a passthrough

    # TODO: Better handle this case
    nil
  end

  defp try_message(%{} = message, :send, %Tornium.Schema.Notification{nid: nid, channel_id: channel_id} = _notification) do
    # NOTE: Could use `Nostrum.Api.request/4` for this function
    # Nostrum.Api.request(:post, Nostrum.Constants.channel_messages(channel_id)

    # Valid keys are listed in https://kraigie.github.io/nostrum/Nostrum.Api.html#create_message/2-options
    case Nostrum.Api.create_message(channel_id, message) do
      {:ok, %Nostrum.Struct.Message{} = resp_message} ->
        # The message was successfully sent...
        # Thus the notification should be deleted as one-shot notifications are deleted once triggered

        Tornium.Schema.Notification
        |> where(nid: ^nid)
        |> Repo.delete()

        {:ok, resp_message}

      {:error, %Nostrum.Error.ApiError{} = error} ->
        # Upon an error, the notification should be disabled with an audit message sent if possible to avoid additional Discord API load

        # TODO: Handle this case
        {:error, error}

      unhandled_value ->
        IO.inspect(unhandled_value)
        # TODO: Handle this case
        {:error, :unknown}
    end
  end

  defp try_message(
         %{} = message,
         :update,
         %Tornium.Schema.Notification{nid: nid, channel_id: channel_id, message_id: message_id} = _notification
       )
       when is_nil(message_id) do
    # This should only occur the first time the notification is triggered

    # Valid keys are listed in https://kraigie.github.io/nostrum/Nostrum.Api.html#create_message/2-options
    case Nostrum.Api.create_message(channel_id, message) do
      {:ok, %Nostrum.Struct.Message{} = resp_message} ->
        # The message was successfully sent...
        # The notification should be updated to include the message ID

        {1, _} =
          Tornium.Schema.Notification
          |> where([n], n.nid == ^nid)
          |> update([n], set: [message_id: ^resp_message.id, channel_id: ^resp_message.channel_id, enabled: true])
          |> Repo.update_all([])

        {:ok, resp_message}

      {:error, %Nostrum.Error.ApiError{} = error} ->
        # Upon an error, the notification should be disabled with an audit message sent if possible to avoid additional Discord API load

        {1, _} =
          Tornium.Schema.Notification
          |> where([n], n.nid == ^nid)
          |> update([n], set: [enabled: false])
          |> Repo.update_all([])

        # TODO: Send audit message
        {:error, error}

      unhandled_value ->
        IO.inspect(unhandled_value)
        # TODO: Disable the notification and send audit message
        {:error, :unknown}
    end
  end

  defp try_message(
         %{} = message,
         :update,
         %Tornium.Schema.Notification{nid: nid, channel_id: channel_id, message_id: message_id} = _notification
       ) do
    # Once the notification is created, the notification's pre-existing message will be updated
    # with the new message. If the message is deleted or can't be updated, a new message will be created.

    case Nostrum.Api.edit_message(channel_id, message_id, message) do
      {:ok, %Nostrum.Struct.Message{} = resp_message} ->
        # The message was successfully updated and no further action is required
        resp_message

      {:error, %Nostrum.Error.ApiError{response: %{code: 10003}} = _error} ->
        # Discord Opcode 10003: Unknown channel
        # The message could be updated as the channel does not exist, so
        #   - Disable the notification
        #   - Send a message to the audit channel if possible

        {1, _} =
          Tornium.Schema.Notification
          |> where([n], n.nid == ^nid)
          |> update([n], set: [message_id: nil, channel_id: nil, enabled: false])
          |> Repo.update_all([])

        # TODO: Send audit message
        nil

      {:error, %Nostrum.Error.ApiError{response: %{code: 10008}} = _error} ->
        # Discord Opcode 10008: Unknown message
        # The message couldn't be updated so
        #   - The message ID should be set to nil
        #   - The message should be recreated

        {1, notification} =
          Tornium.Schema.Notification
          |> select([n], n)
          |> where([n], n.nid == ^nid)
          |> update([n], set: [message_id: nil, enabled: false])
          |> Repo.update_all([])

        try_message(message, :update, notification)

      {:error, %Nostrum.Error.ApiError{} = error} ->
        # TODO: handle this case
        {1, _} =
          Tornium.Schema.Notification
          |> where([n], n.nid == ^nid)
          |> update([n], set: [enabled: false])
          |> Repo.update_all([])

        {:error, error}

      unhandled_value ->
        IO.inspect(unhandled_value)
        # TODO: Handle this case
        {:error, :unknown}
    end
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
      |> where([n], n.nid == ^notification.nid)
      |> update([n], set: [next_execution: ^parse_next_execution(notification)])
      |> Repo.update_all([])

    nil
  end

  @spec generate_lua_state_map(notification :: Tornium.Schema.Notification.t(), response :: map()) :: map()
  defp generate_lua_state_map(
         %Tornium.Schema.Notification{
           parameters: parameters,
           trigger: %Tornium.Schema.Trigger{resource: :user} = _trigger
         } = _notification,
         response
       ) do
    Map.put(parameters, :user, response)
  end

  @spec generate_lua_state_map(notification :: Tornium.Schema.Notification.t(), response :: map()) :: map()
  defp generate_lua_state_map(
         %Tornium.Schema.Notification{
           parameters: parameters,
           trigger: %Tornium.Schema.Trigger{resource: :faction} = _trigger
         } = _notification,
         response
       ) do
    Map.put(parameters, :faction, response)
  end

  @spec generate_lua_state_map(notification :: Tornium.Schema.Notification.t(), response :: map()) :: map()
  defp generate_lua_state_map(
         %Tornium.Schema.Notification{
           parameters: parameters,
           trigger: %Tornium.Schema.Trigger{resource: resource} = _trigger
         } = _notification,
         response
       ) do
    # TODO: Add the remaining resources for `generate_lua_state_map/2`
    parameters
  end
end
