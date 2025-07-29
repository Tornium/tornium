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

defmodule Tornium.Notification do
  require Logger
  alias Tornium.Repo
  import Ecto.Query

  @api_call_priority 10

  @type trigger_resource() :: :user | :faction
  @type render_errors() :: {:error, :template_parse_error | :template_render_error, String.t()}
  @type render_validation_errors :: {:error, :template_decode_error, Jason.DecodeError.t()}

  @doc """
  Execute all notifications against a specific resource (e.g. a certain user ID) with a single API call to retrieve the union.
  """
  @spec execute_resource(
          resource :: trigger_resource(),
          resource_id :: integer(),
          notifications :: [Tornium.Schema.Notification.t()]
        ) :: [Tornium.Lua.trigger_return()] | nil
  def execute_resource(resource, resource_id, notifications) when is_list(notifications) do
    # Determine the union of selections and users for all notifications against a specific resource and resource ID
    {selections, users} =
      Enum.reduce(notifications, {MapSet.new([]), MapSet.new([])}, fn notification, {s, u} ->
        # Use the IDs of admins when the notification is for a Discord server as to avoid issues with missing API keys

        case notification.server do
          nil ->
            # Use this when the notification is not for a server and is intended to be sent through the SSE gateway
            # NOTE: This chunk of the codebase is not implemented yet
            {
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

    restricted = restricted_notification?(notifications)
    api_key = get_api_key(users, resource, resource_id, restricted, notifications)

    case api_key do
      nil ->
        # All notifications need to be disabled at this stage instead of specific notifications
        # given the overall lack of API keys

        nids =
          Enum.map(notifications, fn %Tornium.Schema.Notification{} = notification ->
            Tornium.Notification.Audit.log(:no_api_keys, notification)

            notification.nid
          end)

        Tornium.Schema.Notification
        |> where([n], n.nid in ^nids)
        |> Repo.update_all(set: [enabled: false, error: "No API keys to use"])

        nil

      %Tornium.Schema.TornKey{} ->
        api_response = resource_data(resource, resource_id, MapSet.to_list(selections), api_key)
        # TODO: Better handle Torn error messages before entering each notification

        notifications
        |> Enum.group_by(& &1.trigger)
        |> Enum.map(fn {%Tornium.Schema.Trigger{} = trigger, trigger_notifications} ->
          api_response
          |> filter_response(trigger.resource, trigger.selections)
          |> handle_api_response(trigger, trigger_notifications)
        end)

      {:error, :restricted} ->
        notifications_to_disable =
          Enum.filter(notifications, fn %Tornium.Schema.Notification{} = notification ->
            notification.trigger.restricted_data
          end)

        notification_nids =
          Enum.map(notifications_to_disable, fn %Tornium.Schema.Notification{} = notification ->
            Tornium.Notification.Audit.log(:restricted, notification)

            notification.nid
          end)

        Tornium.Schema.Notification
        |> where([n], n.nid in ^notification_nids)
        |> Repo.update_all(set: [enabled: false, error: ":restricted"])
    end
  end

  @spec get_api_key(
          admins :: [integer()],
          resource :: trigger_resource(),
          resource_id :: integer(),
          restricted :: boolean(),
          notifications :: [Tornium.Schema.Notification.t()]
        ) :: Tornium.Schema.TornKey.t() | nil | {:error, :restricted}
  defp get_api_key(_admins, :faction, resource_id, true, [
         %Tornium.Schema.Notification{server: %Tornium.Schema.Server{} = server} = _notification | _notifications
       ]) do
    faction =
      Tornium.Schema.Faction
      |> where([f], f.tid == ^resource_id)
      |> select([:guild_id])
      |> Repo.one()

    if Enum.member?(server.factions, resource_id) and not is_nil(faction) and faction.guild_id == server.sid do
      Tornium.Schema.TornKey
      |> join(:inner, [k], u in assoc(k, :user), on: u.tid == k.user_id)
      |> where([k, u], k.default == true)
      |> where([k, u], k.disabled == false)
      |> where([k, u], k.paused == false)
      |> where([k, u], u.faction_id == ^resource_id)
      |> where([k, u], u.faction_aa == true)
      |> select([:api_key, :user_id])
      |> first()
      |> Repo.one()
    else
      {:error, :restricted}
    end
  end

  defp get_api_key(admins, :user, resource_id, true, _notifications) do
    if Enum.member?(admins, resource_id) do
      Tornium.Schema.TornKey
      |> where([k], k.user_id == ^resource_id)
      |> where([k, u], k.default == true)
      |> where([k, u], k.disabled == false)
      |> where([k, u], k.paused == false)
      |> select([:api_key, :user_id])
      |> first()
      |> Repo.one()
    else
      {:error, :restricted}
    end
  end

  defp get_api_key(admins, _resource, _resource_id, false, _notifications) when Kernel.length(admins) == 1 do
    Tornium.Schema.TornKey
    |> where([k], k.user_id == ^Enum.at(admins, 0))
    |> where([k, u], k.default == true)
    |> where([k, u], k.disabled == false)
    |> where([k, u], k.paused == false)
    |> select([:api_key, :user_id])
    |> first()
    |> Repo.one()
  end

  defp get_api_key(admins, _resource, _resource_id, false, _notifications) do
    Tornium.Schema.TornKey
    |> where([k], k.user_id in ^MapSet.to_list(admins))
    |> where([k, u], k.default == true)
    |> where([k, u], k.disabled == false)
    |> where([k, u], k.paused == false)
    |> select([:api_key, :user_id])
    |> order_by(fragment("RANDOM()"))
    |> first()
    |> Repo.one()
  end

  # Determine if any of the notifications for this resource + resource ID requires restricted data
  @spec restricted_notification?(notifications :: [Tornium.Schema.Notification.t()]) :: boolean()
  defp restricted_notification?(notifications) do
    Enum.any?(notifications, fn %Tornium.Schema.Notification{
                                  trigger: %Tornium.Schema.Trigger{restricted_data: restricted}
                                } ->
      restricted
    end)
  end

  @spec resource_data(
          resource :: trigger_resource(),
          resource_id :: integer(),
          selections :: [String.t()],
          api_key :: Tornium.Schema.TornKey.t()
        ) :: map() | {:error, any()}
  defp resource_data(:user, resource_id, selections, api_key) do
    # TODO: Create and use types in Tornex for return types
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

  # Filter the API response to only the keys required for the trigger's selection(s).
  @spec filter_response(
          response :: map(),
          resource :: trigger_resource(),
          selections :: [String.t()]
        ) :: map()
  defp filter_response({:error, _}, resource, selections) do
    # FIXME: Better handle this case
    :error
  end

  defp filter_response(response, resource, selections) when is_list(selections) do
    valid_keys =
      Enum.reduce(selections, MapSet.new([]), fn selection, acc ->
        MapSet.union(acc, MapSet.new(Tornium.Notification.Selections.get_selection_keys(resource, selection)))
      end)

    Map.filter(response, fn {key, _value} -> Enum.member?(valid_keys, key) end)
  end

  # Handle the API response by running the notification's Lua code and generate the message
  @spec handle_api_response(
          response :: map(),
          trigger :: Tornium.Schema.Trigger.t(),
          notifications :: [Tornium.Schema.Notification.t()]
        ) :: {:error, Tornium.API.Error.t()} | list(nil)
  defp handle_api_response(:error, _trigger, _notifications) do
    # NOTE: Temporary solution to unknown errors from Tornex
    {:error, :unknown}
  end

  defp handle_api_response(
         %{"error" => %{"code" => code, "error" => error}} = _response,
         _trigger,
         _notifications
       ) do
    {:error, Tornium.API.Error.construct(code, error)}
  end

  defp handle_api_response(%{} = response, trigger, notifications) when is_list(notifications) do
    Enum.map(notifications, fn %Tornium.Schema.Notification{} = notification ->
      Tornium.Lua.execute_lua(trigger.code, generate_lua_state_map(notification, response))
      |> update_passthrough_state(notification)
      |> handle_lua_states(notification)
    end)
  end

  # Handle the returned states (or errors) from the Lua trigger code. If successfully executed, the states will be used
  # to create the message to be sent/updated. If there's an error from the Lua code, the notification will be disabled.
  @spec handle_lua_states(Tornium.Lua.trigger_return(), notification :: Tornium.Schema.Notification.t()) :: nil
  defp handle_lua_states(
         {:ok, [triggered?: true, render_state: %{} = render_state, passthrough_state: %{} = _passthrough_state]},
         %Tornium.Schema.Notification{
           trigger: %Tornium.Schema.Trigger{message_template: trigger_message_template, message_type: :update}
         } = notification
       ) do
    render_message(trigger_message_template, render_state)
    |> validate_message()
    |> try_message(:update, notification)
  end

  defp handle_lua_states(
         {:ok, [triggered?: true, render_state: %{} = render_state, passthrough_state: %{} = _passthrough_state]},
         %Tornium.Schema.Notification{
           trigger: %Tornium.Schema.Trigger{message_template: trigger_message_template, message_type: :send}
         } = notification
       ) do
    render_message(trigger_message_template, render_state)
    |> validate_message()
    |> try_message(:send, notification)
  end

  defp handle_lua_states(
         {:ok, [triggered?: false, render_state: %{} = _render_state, passthrough_state: %{} = _passthrough_state]},
         %Tornium.Schema.Notification{} = _notification
       ) do
    nil
  end

  defp handle_lua_states({:lua_error, error}, %Tornium.Schema.Notification{} = notification) do
    IO.inspect(error, label: ":lua_error [#{notification.nid}]")
    Tornium.Notification.Audit.log(:lua_error, notification)

    Tornium.Schema.Notification
    |> where([n], n.nid == ^notification.nid)
    |> update([n], set: [enabled: false, error: ":lua_error"])
    |> Repo.update_all([])
  end

  defp handle_lua_states(
         {:error, %Tornium.API.Error{} = _torn_error},
         %Tornium.Schema.Notification{} = _notification
       ) do
    # TODO: Handle this error
  end

  defp handle_lua_states({:error, reason}, %Tornium.Schema.Notification{} = _notification) do
    IO.inspect(reason)
    # TODO: Handle this error
    {:error, reason}
  end

  defp handle_lua_states(trigger_return, notification) do
    # Invalid response
    IO.inspect(trigger_return)
    IO.inspect(notification)
    throw(Exception)
  end

  @spec render_message(template :: String.t(), state :: map()) :: String.t() | render_errors()
  def render_message(template, %{} = state) do
    # Attempt to render the JSON message for a notification provided the render state and the Solid template.
    # TODO: Improve the error handling upon errors from Solid
    # TODO: Test this
    # TODO: Document this

    try do
      template
      |> Solid.parse!()
      |> Solid.render!(state)
      |> Kernel.to_string()
      |> String.replace(["\n", "\t"], "")
    rescue
      e in Solid.TemplateError ->
        IO.inspect(e)
        {:error, :template_parse_error, e.message}

      e in Solid.RenderError ->
        IO.inspect(e)
        {:error, :template_render_error, e.message}
    end
  end

  @spec validate_message(message :: String.t() | render_errors()) ::
          map() | render_validation_errors() | render_errors()
  defp validate_message({:error, _, _} = error) do
    error
  end

  defp validate_message(message) when is_binary(message) do
    # Validate the rendered JSON Discord message to avoid unnecessary Discord API calls.

    case Jason.decode(message) do
      {:ok, parsed_message} ->
        parsed_message

      {:error, reason} ->
        {:error, :template_decode_error, reason}
    end
  end

  # Attempt to send or update a message for a notification depending on the notification's configuration
  @spec try_message(
          message :: map() | render_errors() | render_validation_errors(),
          action_type :: :send | :update,
          notification :: Tornium.Schema.Notification.t()
        ) ::
          {:ok, Nostrum.Struct.Message.t()}
          | {:error, :discord_error, Nostrum.Error.ApiError.t()}
          | render_errors()
          | render_validation_errors()
  defp try_message({:error, _, _} = error, _action_type, _notification) do
    error
  end

  defp try_message(%{} = message, :send, %Tornium.Schema.Notification{nid: nid, channel_id: channel_id} = notification) do
    # Valid keys are listed in https://kraigie.github.io/nostrum/Nostrum.Api.html#create_message/2-options
    case Nostrum.Api.Message.create(channel_id, message) do
      {:ok, %Nostrum.Struct.Message{} = resp_message} ->
        # The message was successfully sent...
        # Thus the notification should be deleted as one-shot notifications are deleted once triggered

        Tornium.Schema.Notification
        |> where(nid: ^nid)
        |> Repo.delete()

        {:ok, resp_message}

      {:error, %Nostrum.Error.ApiError{response: %{code: 10_003}} = error} ->
        # Discord Opcode 10003: Unknown channel
        # The message could be updated as the channel does not exist, so
        #   - Disable the notification
        #   - Send a message to the audit channel if possible

        Tornium.Schema.Notification
        |> where([n], n.nid == ^nid)
        |> update([n], set: [channel_id: nil, enabled: false, error: "Unknown channel"])
        |> Repo.update_all([])

        Tornium.Notification.Audit.log(:invalid_channel, notification)
        {:error, :discord_error, error}

      {:error, %Nostrum.Error.ApiError{response: %{code: code}} = error} ->
        # Upon an error, the notification should be disabled with an audit message sent if possible to avoid additional Discord API load

        error_msg = "Nostrum error #{code}"

        Tornium.Schema.Notification
        |> where([n], n.nid == ^nid)
        |> update([n], set: [enabled: false, error: ^error_msg])
        |> Repo.update_all([])

        Tornium.Notification.Audit.log(:discord_error, notification, false, error: error)
        {:error, :discord_error, error}
    end
  end

  # TODO: Handle when the channel_id is nil

  defp try_message(
         %{} = message,
         :update,
         %Tornium.Schema.Notification{nid: nid, channel_id: channel_id, message_id: message_id} = notification
       )
       when is_nil(message_id) do
    # This should only occur the first time the notification is triggered

    # Valid keys are listed in https://kraigie.github.io/nostrum/Nostrum.Api.html#create_message/2-options
    case Nostrum.Api.Message.create(channel_id, message) do
      {:ok, %Nostrum.Struct.Message{} = resp_message} ->
        # The message was successfully sent...
        # The notification should be updated to include the message ID

        Tornium.Schema.Notification
        |> where([n], n.nid == ^nid)
        |> update([n], set: [message_id: ^resp_message.id, channel_id: ^resp_message.channel_id, enabled: true])
        |> Repo.update_all([])

        {:ok, resp_message}

      {:error, %Nostrum.Error.ApiError{response: %{code: 10_003}} = error} ->
        # Discord Opcode 10003: Unknown channel
        # The message could be updated as the channel does not exist, so
        #   - Disable the notification
        #   - Send a message to the audit channel if possible

        Tornium.Schema.Notification
        |> where([n], n.nid == ^nid)
        |> update([n], set: [channel_id: nil, enabled: false, error: "Unknown channel"])
        |> Repo.update_all([])

        Tornium.Notification.Audit.log(:invalid_channel, notification)
        {:error, :discord_error, error}

      {:error, %Nostrum.Error.ApiError{response: %{code: code}} = error} ->
        # Upon an error, the notification should be disabled with an audit message sent if possible to avoid additional Discord API load

        error_msg = "Nostrum error #{code}"

        Tornium.Schema.Notification
        |> where([n], n.nid == ^nid)
        |> update([n], set: [enabled: false, error: ^error_msg])
        |> Repo.update_all([])

        Tornium.Notification.Audit.log(:discord_error, notification, false, error: error)
        {:error, :discord_error, error}
    end
  end

  defp try_message(
         %{} = message,
         :update,
         %Tornium.Schema.Notification{nid: nid, channel_id: channel_id, message_id: message_id} = notification
       ) do
    # Once the notification is created, the notification's pre-existing message will be updated
    # with the new message. If the message is deleted or can't be updated, a new message will be created.

    case Nostrum.Api.Message.edit(channel_id, message_id, message) do
      {:ok, %Nostrum.Struct.Message{} = resp_message} ->
        # The message was successfully updated and no further action is required
        resp_message

      {:error, %Nostrum.Error.ApiError{response: %{code: 10_003}} = error} ->
        # Discord Opcode 10003: Unknown channel
        # The message could be updated as the channel does not exist, so
        #   - Disable the notification
        #   - Send a message to the audit channel if possible

        Tornium.Schema.Notification
        |> where([n], n.nid == ^nid)
        |> update([n], set: [message_id: nil, channel_id: nil, enabled: false, error: "Unknown channel"])
        |> Repo.update_all([])

        Tornium.Notification.Audit.log(:invalid_channel, notification)
        {:error, :discord_error, error}

      {:error, %Nostrum.Error.ApiError{response: %{code: 10_008}} = _error} ->
        # Discord Opcode 10008: Unknown message
        # The message couldn't be updated so
        #   - The message ID should be set to nil
        #   - The message should be recreated

        {1, [notification]} =
          Tornium.Schema.Notification
          |> select([n], n)
          |> where([n], n.nid == ^nid)
          |> update([n], set: [message_id: nil, enabled: false, error: "Unknown message"])
          |> Repo.update_all([])

        try_message(message, :update, notification)

      {:error, %Nostrum.Error.ApiError{response: %{code: code}} = error} ->
        error_msg = "Nostrum error #{code}"

        Tornium.Schema.Notification
        |> where([n], n.nid == ^nid)
        |> update([n], set: [enabled: false, error: ^error_msg])
        |> Repo.update_all([])

        {:error, :discord_error, error}
    end
  end

  @doc """
  Parse the cron tab string of a notification trigger to determine when the next execution will occur.
  """
  @spec parse_next_execution(trigger :: Tornium.Schema.Trigger.t()) :: DateTime.t()
  def parse_next_execution(%Tornium.Schema.Trigger{cron: cron} = _trigger) do
    Crontab.CronExpression.Parser.parse!(cron)
    |> Crontab.Scheduler.get_next_run_date!()
    |> DateTime.from_naive!("Etc/UTC")
  end

  @doc """
  Update the next execution timestamp of the notification.
  """
  @spec update_next_execution(notification :: Tornium.Schema.Trigger.t()) :: nil
  def update_next_execution(%Tornium.Schema.Trigger{tid: trigger_id} = trigger) do
    Tornium.Schema.Trigger
    |> where([t], t.tid == ^trigger_id)
    |> update([t], set: [next_execution: ^parse_next_execution(trigger)])
    |> Repo.update_all([])

    nil
  end

  @spec generate_lua_state_map(notification :: Tornium.Schema.Notification.t(), response :: map()) :: map()
  defp generate_lua_state_map(
         %Tornium.Schema.Notification{
           parameters: parameters,
           trigger: %Tornium.Schema.Trigger{resource: :user} = _trigger,
           previous_state: state
         } = _notification,
         response
       ) do
    parameters
    |> Map.put(:user, response)
    |> Map.put(:state, state)
  end

  @spec generate_lua_state_map(notification :: Tornium.Schema.Notification.t(), response :: map()) :: map()
  defp generate_lua_state_map(
         %Tornium.Schema.Notification{
           parameters: parameters,
           trigger: %Tornium.Schema.Trigger{resource: :faction} = _trigger,
           previous_state: state
         } = _notification,
         response
       ) do
    parameters
    |> Map.put(:faction, response)
    |> Map.put(:state, state)
  end

  @spec generate_lua_state_map(notification :: Tornium.Schema.Notification.t(), response :: map()) :: map()
  defp generate_lua_state_map(
         %Tornium.Schema.Notification{
           parameters: parameters,
           trigger: %Tornium.Schema.Trigger{resource: _resource} = _trigger,
           previous_state: state
         } = _notification,
         _response
       ) do
    # TODO: Add the remaining resources for `generate_lua_state_map/2`
    parameters
    |> Map.put(:state, state)
  end

  @spec update_passthrough_state(Tornium.Lua.trigger_return(), notification :: Tornium.Schema.Notification.t()) ::
          Tornium.Lua.trigger_return()
  defp update_passthrough_state(
         {:ok, [triggered?: true, render_state: %{} = _render_state, passthrough_state: %{} = passthrough_state]} =
           trigger_return,
         %Tornium.Schema.Notification{nid: nid} = _notification
       ) do
    Tornium.Schema.Notification
    |> where([n], n.nid == ^nid)
    |> update([n], set: [previous_state: ^passthrough_state])
    |> Repo.update_all([])

    trigger_return
  end

  defp update_passthrough_state(trigger_return, _notification) do
    trigger_return
  end
end
