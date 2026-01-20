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
  @moduledoc """
  Notification engine built upon `Lua` and `Solid`.
  """

  require Logger
  import Ecto.Query
  alias Tornium.Repo

  @api_call_priority 10

  @typedoc """
  Resources that triggers can be built on top of. These resources represent an in-game "object".
  """
  @type trigger_resource() :: :user | :faction

  @type render_errors() :: {:error, Solid.TemplateError.t() | Solid.RenderError.t()}
  @type render_validation_errors() :: {:error, :template_decode_error, Jason.DecodeError.t()}

  @doc """
  Retrieve a random API key for a set of notifications. If no keys are available, or there is a permissions
  issue, `nil` will be returned.

  If `:restricted?` is true, then only a resource owner's API key will be returned and all notifications that
  don't belong to a resource owner will be disabled.

  Otherwise, depending on the resource type, a random server admin or the resourec owner can be utilized.

  If a notification is disabled due to a permissions issue, all notifications in the group will be skipped
  with a `:skip` return value until the next execution to ensure that only currently enabled notifications
  are executed.
  """
  @spec get_api_key(
          resource :: trigger_resource(),
          resource_id :: integer(),
          restricted? :: boolean(),
          notifications :: [Tornium.Schema.Notification.t()]
        ) :: Tornium.Schema.TornKey.t() | nil | :skip
  def get_api_key(:faction, resource_id, true, notifications) when is_list(notifications) do
    # For notifications against the faction resource utilizing restricted data, all the notifications must be
    # sent to servers that are linked with the faction to avoid the leakage of potentially sensitive data. All
    # other notifications will be disabled with the `:restricted` reason.

    linked_server_id =
      Tornium.Schema.Faction
      |> where([f], f.tid == ^resource_id)
      |> join(:inner, [f], s in assoc(f, :guild), on: f.guild_id == s.tid)
      |> where([f, s], f.tid in s.factions)
      |> select([f, s], f.guild_id)
      |> Repo.one()

    if is_nil(linked_server_id) do
      # There is no linked server or the faction ID does not exist so all notifications must be disabled.
      Tornium.Schema.Notification.disable(notifications, ":restricted")
      # TODO: Send audit message

      nil
    else
      {_valid_notifications, notifications_to_disable} =
        Enum.split_with(notifications, fn notification -> notification.server_id == linked_server_id end)

      # We need to disable notifications that are not for the linked server just so that they don't keep
      # running. Server admins can re-enable them if they want to do so.
      Tornium.Schema.Notification.disable(notifications_to_disable, ":restricted")
      # TODO: Send audit message

      if notifications_to_disable == [] do
        api_keys = Tornium.Schema.Faction.get_api_keys(resource_id)

        case api_keys do
          [] -> nil
          _ -> Enum.random(api_keys)
        end
      else
        :skip
      end
    end
  end

  def get_api_key(:user, resource_id, true, notifications) do
    # For notifications against the user resource utilizing restricted data, all notifications must be created
    # by the resource owner to avoid potentially leaking sensitive data of the user.

    {_valid_notifications, notifications_to_disable} =
      Enum.split_with(notifications, fn notification -> notification.owner_id == resource_id end)

    Tornium.Schema.Notification.disable(notifications_to_disable, ":restricted")
    # TODO: Send audit message

    if notifications_to_disable == [] do
      Tornium.Schema.TornKey
      |> where([k], k.user_id == ^resource_id)
      |> where([k, u], k.default == true)
      |> where([k, u], k.disabled == false)
      |> where([k, u], k.paused == false)
      |> first()
      |> Repo.one()
    else
      :skip
    end
  end

  def get_api_key(_resource, _resource_id, false, notifications) do
    # This is the fallback for all notifications that should operate upon any admin of the server as
    # the data is public and does not reveal non-public information depending on the caller.

    api_key_users =
      notifications
      |> Enum.flat_map(fn
        %Tornium.Schema.Notification{server_id: nil, user_id: user_id} ->
          user_id

        %Tornium.Schema.Notification{server: %Tornium.Schema.Server{admins: server_admins}}
        when is_list(server_admins) ->
          server_admins
      end)
      |> Enum.uniq()

    Tornium.Schema.TornKey
    |> where([k], k.user_id in ^api_key_users)
    |> where([k, u], k.default == true)
    |> where([k, u], k.disabled == false)
    |> where([k, u], k.paused == false)
    |> order_by(fragment("RANDOM()"))
    |> first()
    |> Repo.one()
  end

  # TODO: Add tests
  @doc """
  Determine a list of selections corresponding to the list of notifications.
  """
  @spec get_selections(notifications :: [Tornium.Schema.Notification.t()]) :: [String.t()]
  def get_selections([%Tornium.Schema.Notification{} | _] = notifications) do
    notifications
    |> Enum.map(& &1.trigger.selections)
    |> List.flatten()
    |> Enum.uniq()
  end

  # TODO: Add tests
  @doc """
  Convert the data from notification(s) to a `Tornex.Query` to fetch the data for the notification(s).
  """
  @spec to_query(
          resource :: trigger_resource(),
          resource_id :: integer(),
          selections :: [String.t()],
          api_key :: Tornium.Schema.TornKey.t()
        ) :: Tornex.Query.t()
  def to_query(
        :user,
        resource_id,
        selections,
        %Tornium.Schema.TornKey{api_key: api_key, user_id: api_key_owner}
      )
      when is_list(selections) and is_binary(api_key) and is_integer(api_key_owner) do
    %Tornex.Query{
      resource: "user",
      resource_id: resource_id,
      selections: selections,
      key: api_key,
      key_owner: api_key_owner,
      nice: @api_call_priority
    }
  end

  def to_query(
        :faction,
        resource_id,
        selections,
        %Tornium.Schema.TornKey{api_key: api_key, user_id: api_key_owner}
      )
      when is_list(selections) and is_binary(api_key) and is_integer(api_key_owner) do
    %Tornex.Query{
      resource: "faction",
      resource_id: resource_id,
      selections: selections,
      key: api_key,
      key_owner: api_key_owner,
      nice: @api_call_priority
    }
  end

  # TODO: Test this
  @doc """
  Filter the API response to only the keys required for the trigger's selection(s).
  """
  @spec filter_response(
          response :: %{String.t() => term()},
          resource :: trigger_resource(),
          selections :: [String.t()]
        ) :: %{String.t() => term()}
  def filter_response(response, resource, selections) when is_list(selections) do
    valid_keys =
      selections
      |> Enum.map(&Tornium.Notification.Selections.get_selection_keys(resource, &1))
      |> List.flatten()
      |> Enum.uniq()

    Map.filter(response, fn {key, _value} -> Enum.member?(valid_keys, key) end)
  end

  @doc """
  Handle the API response by running the notification's Lua code and generate the message.

  For each notification, this will perform the following steps:
    - Configure a Lua VM with the API response, notification parameters, and the current notification state
    - Execute the notification trigger's Lua code in the Lua VM
    - Update the passthrough state of the notification
    - Render the message from the render state
    - Validate the rendered message JSON
    - Attempt to send/update the message
  """
  @spec handle_api_response(
          response :: %{String.t() => term()},
          trigger :: Tornium.Schema.Trigger.t(),
          notifications :: [Tornium.Schema.Notification.t()]
        ) :: :ok
  def handle_api_response(%{} = response, trigger, notifications) when is_list(notifications) do
    Enum.each(notifications, fn %Tornium.Schema.Notification{} = notification ->
      Tornium.Notification.Lua.execute_lua(trigger.code, generate_lua_state_map(notification, response))
      |> update_passthrough_state(notification)
      |> handle_lua_states(notification)
    end)
  end

  # Handle the returned states (or errors) from the Lua trigger code. If successfully executed, the
  # states will be used to create the message to be sent/updated. If there's an error from the
  # Lua code, the notification will be disabled.
  @spec handle_lua_states(
          Tornium.Notification.Lua.trigger_return(),
          notification :: Tornium.Schema.Notification.t()
        ) :: nil
  defp handle_lua_states(
         {:ok, [triggered?: true, render_state: %{} = render_state, passthrough_state: %{} = _passthrough_state]},
         %Tornium.Schema.Notification{server_id: server_id} = notification
       )
       when not is_nil(server_id) do
    with {:ok, rendered} <- Tornium.Notification.Delivery.Discord.render(render_state, notification),
         {:ok, validated} <- Tornium.Notification.Delivery.Discord.validate(rendered),
         {:ok, output} <- Tornium.Notification.Delivery.Discord.deliver(validated, notification) do
      {:ok, output}
    end
  end

  defp handle_lua_states(
         {:ok, [triggered?: true, render_state: %{} = render_state, passthrough_state: %{} = _passthrough_state]},
         %Tornium.Schema.Notification{server_id: server_id} = notification
       )
       when not is_nil(server_id) do
  end

  defp handle_lua_states(
         {:ok, [triggered?: false, render_state: %{} = _render_state, passthrough_state: %{} = _passthrough_state]},
         %Tornium.Schema.Notification{} = _notification
       ) do
    # Since the Lua code did not trigger the notification, we are not going to do anything here and ignore everything.
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

  defp handle_lua_states({:error, reason}, %Tornium.Schema.Notification{} = _notification) do
    reason
    |> inspect(label: "Notification error reason")
    |> Logger.info()

    # TODO: Handle this error
    {:error, reason}
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

  @spec update_passthrough_state(
          Tornium.Notification.Lua.trigger_return(),
          notification :: Tornium.Schema.Notification.t()
        ) ::
          Tornium.Notification.Lua.trigger_return()
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
