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
          [Nostrum.Api.error()] | [{:ok, Nostrum.Struct.Message.t()}] | nil
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
       ) when is_list(message_tasks) do
    opts =
      message
      |> Map.from_struct()
      |> Map.to_list()
      |> Keyword.delete(:channel_id)

    task =
      Task.Supervisor.async_nolink(Tornium.TornexTaskSupervisor, fn ->
        Nostrum.Api.Message.create(channel_id, opts)
      end)

    send_each_message(remaining_messages, [task | message_tasks])
  end

  defp send_each_message([], message_tasks) when is_list(message_tasks) do
    message_tasks
  end

  @doc """
  Chunk a list of embeds into a list of messages.

  ## Options
    * `:chunk_size` - Maximum number of embeds in a chunk
    * `:channel` - Channel the message will be sent to (Optional)
  """
  @spec chunk_embeds(embeds :: [Nostrum.Struct.Embed.t()], opts :: keyword()) :: [Nostrum.Struct.Message.t()]
  def chunk_embeds([%Nostrum.Struct.Embed{} | _] = embeds, opts \\ []) do
    chunk_size = Keyword.get(opts, :chunk_size, 10)
    channel = Keyword.get(opts, :channel, nil)

    embeds
    |> Enum.chunk_every(chunk_size)
    |> Enum.map(fn overdose_embed_chunks when is_list(overdose_embed_chunks) ->
      %Nostrum.Struct.Message{channel_id: channel, embeds: overdose_embed_chunks}
    end)
  end

  @doc """
  Create a string of role mentions from a list of Discord roles.

  If a role is an assignable role, the assignable role will be replaced with the roles provided in `opts.assigns`
  if provided. If no `assigns` are provided or `-1` is not included in the list of roles, the assignable role
  will not be included in the created string of role mentions.

  ## Options
    * `:assigns` - List of role IDs or `{:user, user Discord ID}`

  ## Examples

    iex> Tornium.Discord.roles_to_string([1, 2, 3])
    "<@&1> <@&2> <@&3>"

    iex> Tornium.Discord.roles_to_string([1, -1], assigns: [1, 2])
    "<@&1> <@&2>"

    iex> Tornium.Discord.roles_to_string([1, nil, -1], assigns: [2, nil, {:user, 3}, {:user, nil}])
    "<@&1> <@&2> <@3>"
  """
  @spec roles_to_string(roles :: [Tornium.Discord.role_assignable()], opts :: keyword()) :: String.t()
  def roles_to_string(roles, opts \\ []) when is_list(roles) do
    roles
    |> set_assigned_role(opts)
    |> List.flatten()
    |> Enum.uniq()
    |> Enum.reject(fn
      role when is_nil(role) -> true
      {:user, user_id} when is_nil(user_id) -> true
      _ -> false
    end)
    |> Enum.map_join(" ", fn
      role_id when is_integer(role_id) -> "<@&#{role_id}>"
      {:user, user_id} when is_integer(user_id) -> "<@#{user_id}>"
    end)
  end

  @spec set_assigned_role(roles :: [Tornium.Discord.role_assignable()], opts :: keyword()) :: [Tornium.Discord.role()]
  defp set_assigned_role(roles, opts) do
    assigns = Keyword.get(opts, :assigns, [])

    if Enum.member?(roles, -1) do
      Enum.map(roles, fn
        -1 -> assigns
        role -> role
      end)
    else
      roles
    end
  end
end
