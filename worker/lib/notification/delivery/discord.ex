defmodule Tornium.Notification.Delivery.Discord do
  import Ecto.Query
  alias Tornium.Repo

  @behaviour Tornium.Notification.Delivery

  @impl true
  def render(
        state,
        %Tornium.Schema.Notification{
          trigger: %Tornium.Schema.Trigger{message_template: template}
        } = _notification
      )
      when is_map(state) and is_binary(template) do
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
        e
        |> inspect(label: "Template parse error")
        |> Logger.debug()

        {:error, e}

      e in Solid.RenderError ->
        e
        |> inspect(label: "Template render error")
        |> Logger.debug()

        {:error, e}
    end
  end

  @impl true
  def validate(rendered) when is_binary(rendered) do
    # We want to validate the rendered JSON Discord message to avoid unnecessary Discord API calls
    # that would fail.

    # For now, just decoding the message is sufficient, but in the future we could validate
    # aspects such as the message length, embed count, etc.
    JSON.decode(rendered)
  end

  @impl true
  def deliver(
        rendered,
        %Tornium.Schema.Notification{trigger: %Tornium.Schema.Trigger{message_type: message_type}} = notification
      )
      when is_map(rendered) do
    try_message(rendered, message_type, notification)
  end

  defp try_message(
         %{} = message,
         :send,
         %Tornium.Schema.Notification{nid: nid, channel_id: channel_id, one_shot: one_shot?} = notification
       ) do
    # Valid keys are listed in https://kraigie.github.io/nostrum/Nostrum.Api.html#create_message/2-options
    case Nostrum.Api.Message.create(channel_id, message) do
      {:ok, %Nostrum.Struct.Message{} = resp_message} ->
        # The message was successfully sent...
        # Thus the notification should be deleted as one-shot notifications are deleted once triggered

        if one_shot? do
          Tornium.Schema.Notification
          |> where(nid: ^nid)
          |> Repo.delete_all()
        end

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
end
