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

defmodule Tornium.Telemetry.VerificationLogs do
  @moduledoc """
  Store `:telemetry` events related to verification on the database.

  See `Tornium.Telemetry` for information on the telemetry events handled by this module.
  """

  use GenServer

  @handler_id "tornium-verification-telemetry-handler"
  @default_write_interval 15_000
  @write_table :tornium_verification_telemetry_logs_queue

  @typedoc """
  Tuple used to store verification logs in the ETS table
  """
  @type ets_log() ::
          {discord_id :: pos_integer() | nil, user_id :: pos_integer() | nil, log :: Tornium.Schema.VerificationLog.t()}

  @doc """
  Attaches the Tornium `:telemetry` handler for verification logs.
  """
  @spec attach_logger(opts :: keyword()) :: :ok | {:error, :already_exists}
  def attach_logger(opts \\ []) do
    events = [
      [:tornium, :guild, :verify, :success],
      [:tornium, :guild, :verify, :failure]
    ]

    opts =
      opts
      |> Keyword.put_new(:encode, true)
      |> Keyword.put_new(:level, :info)

    :telemetry.attach_many(@handler_id, events, &__MODULE__.handle_event/4, opts)
  end

  @doc """
  Detaches the Tornium `:telemetry` handler for verification logs.
  """
  @spec detach_logger() :: :ok | {:error, :not_found}
  def detach_logger() do
    :telemetry.detach(@handler_id)
  end

  @doc false
  def handle_event(
        [:tornium, :guild, :verify, :failure],
        %{} = _measurements,
        %{
          guild_id: guild_id,
          user_id: user_id,
          discord_id: discord_id,
          error_type: error_type,
          error_code: error_code,
          error_message: error_message
        } = _metadata,
        _opts
      ) do
    insert(guild_id, %Tornium.Schema.VerificationLog{
      server_id: guild_id,
      discord_id: discord_id,
      user_id: user_id,
      error_type: error_type,
      error_code: error_code,
      error_message: error_message
    })
  end

  @doc false
  def handle_event(
        [:tornium, :guild, :verify, :success],
        %{} = _measurements,
        %{
          guild_id: guild_id,
          user_id: user_id,
          discord_id: discord_id,
          old_nickname: old_nickname,
          new_nickname: new_nickname,
          added_roles: added_roles,
          removed_roles: removed_roles
        },
        _opts
      ) do
    insert(guild_id, %Tornium.Schema.VerificationLog{
      server_id: guild_id,
      discord_id: discord_id,
      user_id: user_id,
      old_nickname: old_nickname,
      new_nickname: new_nickname,
      roles_added: added_roles,
      roles_removed: removed_roles
    })
  end

  @doc false
  def handle_event([:tornium | _], _measurements, _metadata, _opts) do
    :ok
  end

  @doc """
  Start the GenServer to write verification logs.

  ## Options
    * `:write_interval` - Milliseconds between log writes (default: `@default_write_interval`)
  """
  @spec start_link(opts :: keyword()) :: GenServer.on_start()
  def start_link(opts \\ []) do
    GenServer.start_link(__MODULE__, opts, name: __MODULE__)
  end

  @impl true
  def init(opts \\ []) do
    write_interval = Keyword.get(opts, :write_interval, @default_write_interval)
    timer = start_timer(write_interval)
    create_table()

    {:ok, %{write_interval: write_interval, write_timer: timer}}
  end

  @impl true
  def handle_info(:write_logs, %{write_interval: interval} = state) do
    state = %{state | write_timer: start_timer(interval)}

    Enum.each(take(), fn {_guild_id, logs} -> write_logs(logs) end)

    # TODO: Create a worker to send messages to log channels from the database logs if it is enabled for the server

    {:noreply, state}
  end

  @spec start_timer(duration :: pos_integer()) :: reference()
  defp start_timer(duration) when is_integer(duration) do
    Process.send_after(self(), :write_logs, duration)
  end

  @spec create_table() :: :ets.table()
  defp create_table() do
    :ets.new(@write_table, [:named_table, :duplicate_bag, :public])
  end

  @doc false
  @spec insert(guild_id :: pos_integer(), log :: Tornium.Schema.VerificationLog.t(), opts :: keyword()) :: term()
  def insert(guild_id, log, opts \\ []) when is_integer(guild_id) and not is_nil(log) do
    discord_id = Keyword.get(opts, :discord_id)
    user_id = Keyword.get(opts, :user_id)
    table = Keyword.get(opts, :table, @write_table)

    :ets.insert(table, {guild_id, {discord_id, user_id, log}})
  end

  @doc false
  @spec take(table :: :ets.table()) :: %{pos_integer() => [ets_log()]}
  def take(table \\ @write_table) do
    table
    |> take_guilds()
    |> Enum.map(fn guild_id ->
      {
        guild_id,
        table
        |> :ets.take(guild_id)
        |> Enum.map(fn {_k, v} -> v end)
      }
    end)
    |> Map.new()
  end

  @doc false
  @spec take_guilds(table :: :ets.table()) :: MapSet.t(pos_integer())
  def take_guilds(table \\ @write_table) do
    table
    |> :ets.select([{{:"$1", :_}, [], [:"$1"]}])
    |> MapSet.new()
  end

  @doc false
  @spec write_logs(guild_logs :: [ets_log()]) :: term()
  def write_logs(guild_logs) when is_list(guild_logs) do
    guild_logs
    |> Enum.map(fn {_discord_id, _user_id, %Tornium.Schema.VerificationLog{} = log} -> log end)
    |> Tornium.Schema.VerificationLog.insert_all()
  end
end
