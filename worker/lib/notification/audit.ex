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

defmodule Tornium.Notification.Audit do
  require Logger
  import Ecto.Query
  import Nostrum.Struct.Embed
  alias Tornium.Repo

  @type actions :: :no_api_keys | :lua_error | :invalid_channel | :discord_error | :restricted

  @doc """
  Log a notification action in the audit log. If there is an audit channel for the notification's server, a message will also be sent there.

  # Channel ID
  integer(): Sends a message to the audit channel if possible 
  nil: Does nothing
  false: Creates a log message and sends a message to the audit channel if possible 
  """
  @spec log(
          action :: actions(),
          notification :: Tornium.Schema.Notification.t(),
          channel_id :: integer() | nil | false,
          opts: Keyword.t()
        ) :: nil
  def log(action, notification, channel_id \\ false, opts \\ [])

  def log(_action, %Tornium.Schema.Notification{} = _notification, channel_id, _opts) when is_nil(channel_id) do
    # General default case for when there is no audit log channel or any server associated with the notification
    nil
  end

  def log(:no_api_keys = action, %Tornium.Schema.Notification{} = notification, channel_id, opts)
      when channel_id == false do
    "No API keys were available for the notification"
    |> format_log(notification, action)
    |> Logger.info()

    audit_channel = get_audit_channel(notification)
    log(action, notification, audit_channel, opts)

    nil
  end

  def log(:no_api_keys = action, %Tornium.Schema.Notification{nid: nid} = _notification, channel_id, _opts)
      when is_integer(channel_id) do
    create_audit_message(
      channel_id,
      action,
      "[#{nid}] There were API keys available to perform this notification and it has been disabled."
    )

    nil
  end

  def log(:lua_error = action, %Tornium.Schema.Notification{} = notification, channel_id, opts)
      when channel_id == false do
    "An error occurred in the Trigger's Lua code"
    |> format_log(notification, action)
    |> Logger.info()

    audit_channel = get_audit_channel(notification)
    log(action, notification, audit_channel, opts)

    nil
  end

  def log(:lua_error = action, %Tornium.Schema.Notification{nid: nid} = _notification, channel_id, _opts)
      when is_integer(channel_id) do
    create_audit_message(
      channel_id,
      action,
      "[#{nid}] An error occured in the trigger's Lua code. The trigger's developer should contact tiksan for the error message."
    )

    nil
  end

  def log(:invalid_channel = action, %Tornium.Schema.Notification{} = notification, channel_id, opts)
      when channel_id == false do
    "The channel for the notification could not be found"
    |> format_log(notification, action)
    |> Logger.info()

    audit_channel = get_audit_channel(notification)
    log(action, notification, audit_channel, opts)

    nil
  end

  def log(:invalid_channel = action, %Tornium.Schema.Notification{nid: nid} = _notification, channel_id, _opts)
      when is_integer(channel_id) do
    create_audit_message(
      channel_id,
      action,
      "[#{nid}] The channel for this notification could not be found when a message was being sent."
    )

    nil
  end

  def log(:discord_error = action, %Tornium.Schema.Notification{} = notification, channel_id, opts)
      when channel_id == false do
    %Nostrum.Error.ApiError{response: %{code: error_code}} = Keyword.fetch!(opts, :error)

    "A Discord error (#{error_code}) occurred while making an API call"
    |> format_log(notification, action)
    |> Logger.info()

    if error_code == 50_035 do
      opts
      |> Keyword.fetch!(:error)
      |> inspect(label: "[50035 error]")
      |> Logger.warning()

      opts
      |> Keyword.fetch!(:message)
      |> inspect(label: "[50035 message]")
      |> Logger.warning()
    end

    audit_channel = get_audit_channel(notification)
    log(action, notification, audit_channel, opts)

    nil
  end

  def log(:discord_error = action, %Tornium.Schema.Notification{nid: nid} = _notification, channel_id, opts)
      when is_integer(channel_id) do
    %Nostrum.Error.ApiError{response: %{code: error_code}} = Keyword.fetch!(opts, :error)

    create_audit_message(
      channel_id,
      action,
      "[#{nid}] An unhandled Discord error (#{error_code}) occured during the handling of this notification. You will need to re-enable this notification."
    )

    nil
  end

  def log(:restricted = action, %Tornium.Schema.Notification{} = notification, channel_id, opts)
      when channel_id == false do
    "Restricted data unavailable"
    |> format_log(notification, action)
    |> Logger.info()

    audit_channel = get_audit_channel(notification)
    log(action, notification, audit_channel, opts)

    nil
  end

  def log(
        :restricted = action,
        %Tornium.Schema.Notification{
          nid: nid,
          resource_id: resource_id,
          trigger: %Tornium.Schema.Trigger{resource: :faction}
        } = _notification,
        channel_id,
        _opts
      )
      when is_integer(channel_id) do
    create_audit_message(
      channel_id,
      action,
      "[#{nid}] The resource required for this notification is restricted. The faction (#{resource_id}) must be linked to this server and there must be an AA member of that faction signed into Tornium for this notification to work."
    )

    nil
  end

  def log(
        :restricted = action,
        %Tornium.Schema.Notification{
          nid: nid,
          resource_id: resource_id,
          trigger: %Tornium.Schema.Trigger{resource: :user}
        } = _notification,
        channel_id,
        _opts
      )
      when is_integer(channel_id) do
    create_audit_message(
      channel_id,
      action,
      "[#{nid}] The resource required for this notification is restricted. The user (#{resource_id}) must be an admin in this server for this notification to work."
    )

    nil
  end

  @doc """
  Format the notification-related log message
  """
  @spec format_log(message :: String.t(), notification :: Tornium.Schema.Notification.t(), action :: atom()) ::
          String.t()
  def format_log(message, %Tornium.Schema.Notification{nid: nid} = _notification, action) do
    "[#{nid}] :#{action} - #{message}"
  end

  @spec get_audit_channel(notification :: Tornium.Schema.Notification.t()) :: pos_integer() | nil
  defp get_audit_channel(%Tornium.Schema.Notification{server_id: nil} = _notification) do
    nil
  end

  defp get_audit_channel(%Tornium.Schema.Notification{server_id: server_id}) do
    config =
      Tornium.Schema.ServerNotificationsConfig
      |> select([c], c.log_channel)
      |> where([c], c.server_id == ^server_id)
      |> Repo.one()

    case config do
      nil ->
        nil

      %Tornium.Schema.ServerNotificationsConfig{log_channel: log_channel} = _ ->
        log_channel

      log_channel when is_integer(log_channel) ->
        log_channel
    end
  end

  @spec create_audit_message(
          audit_channel :: integer() | nil,
          action :: atom(),
          description :: String.t(),
          color :: integer() | nil
        ) :: {:ok, Nostrum.Struct.Message.t()} | Nostrum.Api.error() | nil
  defp create_audit_message(audit_channel, action, description, color \\ nil)

  defp create_audit_message(audit_channel, _action, _description, _color) when is_nil(audit_channel) do
    nil
  end

  defp create_audit_message(audit_channel, action, description, color) when is_integer(audit_channel) do
    now =
      DateTime.utc_now()
      |> DateTime.to_iso8601()

    embed =
      %Nostrum.Struct.Embed{}
      |> put_title("Notification Audit Log - :#{Atom.to_string(action)}")
      |> put_description(description)
      |> put_timestamp(now)
      |> put_color(color || Tornium.Discord.Constants.colors()[:good])

    Nostrum.Api.Message.create(audit_channel, embeds: [embed])
  end
end
