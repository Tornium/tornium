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

defmodule Tornium.Discord do
  @typedoc """
  Discord role ID.
  """
  @type role :: non_neg_integer()

  @typedoc """
  Discord role ID that may be assigned during the usage of the Discord role.

  The value is either a Discord role or -1. When the value is -1, the value will be replaced with any number of
  Discord role IDs when rendering a list of roles as a String with `Tornium.Utils.roles_to_string/1`.
  """
  @type role_assignable :: role() | -1

  @doc ~S"""
  Asynchronously send a list of messages with the option of returning the responses.

  This function must be used to send the messages asynchronously as the underlying API is synchronous. The `collect` option must be `true` to synchronously collect and return the API responses.

  ## Options
    * `:collect` - A boolean to get the responses from all message create requests (default: `false`).
    * `:timeout` - The timeout in milliseconds (default: `:infinity`).
  """
  @spec send_messages(messages :: [Nostrum.Struct.Message.t()], opts :: Keyword) ::
          [Nostrum.Api.error() | {:ok, Nostrum.Struct.Message.t()}] | nil
  def send_messages(messages, opts \\ []) when is_list(messages) do
    collect = Keyword.get(opts, :collect, false)
    timeout = Keyword.get(opts, :timeout, :infinity)

    tasks = send_each_message(messages)

    if collect do
      Task.await_many(tasks, timeout)
    else
      nil
    end
  end

  @spec send_each_message(messages :: [Nostrum.Struct.Message.t()], message_tasks :: [Task.t()]) :: [Task.t()]
  defp send_each_message(messages, message_tasks \\ [])

  defp send_each_message(
         [%Nostrum.Struct.Message{channel_id: channel_id} = message | remaining_messages],
         message_tasks
       ) do
    opts =
      message
      |> Map.from_struct()
      |> Map.to_list()
      |> Keyword.delete(:channel_id)

    task =
      Task.Supervisor.async_nolink(Tornium.TornexTaskSupervisor, fn -> Nostrum.Api.Message.create(channel_id, opts) end)

    send_each_message(remaining_messages, [task | message_tasks])
  end

  defp send_each_message([], message_tasks) do
    message_tasks
  end
end
