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

defmodule Tornium.Workers.VerificationDiscordNotifications do
  @moduledoc """
  Send Discord notifications for verification logs.

  If a Discord server has a verification log channel configured, this job will send the
  notifications for the `Tornium.Schema.VerificationLog` logs for the Discord server
  since the last time the worker ran (either succesfully or not).
  """

  alias Tornium.Repo
  import Ecto.Query

  use Oban.Worker,
    max_attempts: 3,
    priority: 0,
    queue: :guild_processing,
    tags: ["guild"],
    unique: [
      period: :infinity,
      fields: [:worker],
      states: :incomplete
    ]

  @max_log_interval _seconds = 3_600
  @max_message_size _characters = 2000

  @impl Oban.Worker
  def perform(%Oban.Job{} = _job) do
    Tornium.Schema.VerificationLog
    |> where([l], l.timestamp >= ^last_attempt())
    |> join(:inner, [l], s in assoc(l, :server), on: l.server_id == s.sid)
    |> where([l, s], not is_nil(s.verify_log_channel) and s.verify_log_channel > 0)
    |> Repo.all()
    |> Enum.group_by(& &1.server_id)
    |> Enum.each(&send_guild_logs/1)

    :ok
  end

  # TEST: Test last_attempt/0
  @doc """
  Get the last attempt timestmap of sending verification logs.

  If there has been no attempt to send a verification log notification within the last
  `@max_log_interval` seconds, `@max_log_interval` seconds ago will be considered the last
  attempt to avoid sending too many unnescessary notifications.
  """
  @spec last_attempt() :: DateTime.t() | nil
  def last_attempt() do
    # We only want to use jobs of this worker that have "finished" running, either successfully
    # or not, when considering its last attempt timestamp. See Oban.Jobstates/0 for a list of the
    # job states.
    job =
      Oban.Job.query(worker: __MODULE__, state: ~w(completed discarded cancelled))
      |> order_by(desc: :scheduled_at)
      |> first()
      |> Repo.one()

    job_timestamp = job && (job.completed_at || job.discarded_at || job.cancelled_at)
    min_timestamp = DateTime.add(DateTime.utc_now(), -@max_log_interval, :second)

    if not is_nil(job_timestamp) and DateTime.after?(job_timestamp, min_timestamp) do
      job_timestamp
    else
      min_timestamp
    end
  end

  @spec send_guild_logs({guild_id :: pos_integer(), logs :: [Tornium.Schema.VerificationLog.t()]}) :: term()
  defp send_guild_logs({guild_id, logs}) when is_integer(guild_id) and is_list(logs) do
    {success_logs, error_logs} = Enum.split_with(logs, &is_nil(&1.error_type))

    log_channel_id =
      Tornium.Schema.Server
      |> where([s], s.sid == ^guild_id)
      |> select([s], s.verify_log_channel)
      |> Repo.one!()

    error_logs
    |> Enum.map(&log_to_string/1)
    |> Enum.reject(&is_nil/1)
    |> to_messages(log_channel_id)
    |> Tornium.Discord.send_messages(timeout: _milliseconds = 30_000)

    success_logs
    |> Enum.map(&log_to_string/1)
    |> Enum.reject(&is_nil/1)
    |> to_messages(log_channel_id)
    |> Tornium.Discord.send_messages(timeout: _milliseconds = 30_000)
  end

  # TEST: Test log_to_string/1
  @doc false
  @spec log_to_string(log :: Tornium.Schema.VerificationLog.t()) :: String.t()
  def log_to_string(
        %Tornium.Schema.VerificationLog{
          discord_id: discord_id,
          roles_added: roles_added,
          roles_removed: roles_removed,
          old_nickname: old_nickname,
          new_nickname: new_nickname,
          error_type: error_type
        } = _log
      )
      when is_integer(discord_id) and is_nil(error_type) do
    changes =
      [
        if(old_nickname != new_nickname, do: "Nickname Updated"),
        if(roles_added != [], do: "+#{length(roles_added)} Roles"),
        if(roles_removed != [], do: "-#{length(roles_removed)} Roles")
      ]
      |> Enum.reject(&is_nil/1)

    if changes == [],
      do: "<@#{discord_id}>: Verified",
      else: "<@#{discord_id}>: Verified (#{changes |> Enum.join(",")})"
  end

  def log_to_string(%Tornium.Schema.VerificationLog{discord_id: discord_id, error_type: :unverified}) do
    "<@#{discord_id}>: Not Verified"
  end

  def log_to_string(%Tornium.Schema.VerificationLog{
        discord_id: discord_id,
        error_type: :discord_permission,
        error_code: error_code
      }) do
    "<@#{discord_id}>: Discord Permissions Error (#{error_code})"
  end

  def log_to_string(%Tornium.Schema.VerificationLog{discord_id: discord_id, error_type: :no_api_key}) do
    "<@#{discord_id}>: No API Key"
  end

  def log_to_string(%Tornium.Schema.VerificationLog{
        discord_id: discord_id,
        error_type: :config,
        error_message: error_message
      }) do
    "<@#{discord_id}>: Misconfigured (#{error_message})"
  end

  def log_to_string(%Tornium.Schema.VerificationLog{
        discord_id: discord_id,
        error_type: :torn_api,
        error_code: error_code
      }) do
    "<@#{discord_id}>: Torn API Error (#{error_code})"
  end

  def log_to_string(%Tornium.Schema.VerificationLog{
        discord_id: discord_id,
        error_type: :discord_api,
        error_code: error_code
      }) do
    "<@#{discord_id}>: Discord API Error (#{error_code})"
  end

  @spec to_messages(log_strings :: [String.t()], channel_id :: pos_integer()) :: [Nostrum.Struct.Message.t()]
  defp to_messages(log_strings, channel_id) when is_list(log_strings) and is_integer(channel_id) do
    log_strings
    |> Enum.chunk_while(
      [],
      fn log_string, acc ->
        current_length =
          acc
          |> Enum.join("\n")
          |> String.length()

        if current_length + String.length(log_string) <= @max_message_size do
          {:cont, acc ++ [log_string]}
        else
          {:cont, acc, [log_string]}
        end
      end,
      fn
        [] -> {:cont, []}
        acc -> {:cont, acc, []}
      end
    )
    |> Enum.map(
      &%Nostrum.Struct.Message{
        channel_id: channel_id,
        content: Enum.join(&1, "\n")
      }
    )
  end
end
