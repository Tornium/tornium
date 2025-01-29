defmodule Tornium.Notification.Audit do
  require Logger
  import Ecto.Query
  import Nostrum.Struct.Embed
  alias Tornium.Repo

  @type actions :: :no_api_keys | :lua_error | :invalid_channel | :discord_error

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
          opts: Keyword
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
  end

  def log(:discord_error = action, %Tornium.Schema.Notification{} = notification, channel_id, opts)
      when channel_id == false do
    %Nostrum.Error.ApiError{response: %{code: error_code}} = opts.error

    "A Discord error (#{error_code}) occurred while making an API call"
    |> format_log(notification, action)
    |> Logger.info()

    audit_channel = get_audit_channel(notification)
    log(action, notification, audit_channel, opts)

    nil
  end

  def log(:discord_error = action, %Tornium.Schema.Notification{nid: nid} = _notification, channel_id, opts)
      when is_integer(channel_id) do
    %Nostrum.Error.ApiError{response: %{code: error_code}} = opts.error

    create_audit_message(
      channel_id,
      action,
      "[#{nid}] An unhandled Discord error (#{error_code}) occured during the handling of this notification. You will need to re-enable this notification."
    )
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

  defp get_audit_channel(%Tornium.Schema.Notification{server: server_id}) do
    # TODO: Add caching to this
    # Probably use LRU caching with TTL
    # https://github.com/whitfin/cachex

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
    end
  end

  @spec create_audit_message(
          audit_channel :: integer(),
          action :: atom(),
          description :: String.t(),
          color :: integer() | nil
        ) :: {:ok, Nostrum.Struct.Message.t()} | Nostrum.Api.error()
  defp create_audit_message(audit_channel, action, description, color \\ nil) do
    now =
      DateTime.utc_now()
      |> DateTime.to_iso8601()

    embed =
      %Nostrum.Struct.Embed{}
      |> put_title("Notification Audit Log - :#{Atom.to_string(action)}")
      |> put_description(description)
      |> put_timestamp(now)
      |> put_color(color || Tornium.Discord.Constants.colors()[:good])

    Nostrum.Api.create_message(audit_channel, embeds: [embed])
  end
end
