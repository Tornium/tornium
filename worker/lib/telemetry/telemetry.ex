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

defmodule Tornium.Telemetry do
  @moduledoc false

  require Logger

  @handler_id "tornium-telemetry-hndler"

  @doc """
  Attaches the default Tornium `:telemetry` handler.
  """
  @spec attach_default_logger(opts :: Keyword.t()) :: :ok | {:error, :already_exists}
  def attach_default_logger(opts \\ []) when is_list(opts) do
    events = [
      [:tornium, :oc_team, :member_removed]
    ]

    opts =
      opts
      |> Keyword.put_new(:encode, true)
      |> Keyword.put_new(:level, :info)

    :telemetry.attach_many(@handler_id, events, &__MODULE__.handle_event/4, opts)
  end

  @doc """
  Detaches the default Tornium `:telemetry` handler.
  """
  @spec detach_default_logger() :: :ok | {:error, :not_found}
  def detach_default_logger() do
    :telemetry.detach(@handler_id)
  end

  @doc false
  def handle_event(
        [:tornium, :oc_team, :member_removed],
        %{} = _measurements,
        %{user_id: user_id, team_id: team_id, faction_id: faction_id} = _metadata,
        opts
      ) do
    opts
    |> Keyword.put(:level, :info)
    |> log(%{
      event: "oc_team:member_removed",
      message: "#{user_id} was removed from their OC team",
      user_id: user_id,
      team_id: team_id,
      faction_id: faction_id
    })
  end

  @doc false
  def handle_event(
        [:tornium, :bot, :guild_joined],
        %{} = _measurements,
        %{guild_id: guild_id, guild_name: guild_name} = _metadata,
        opts
      ) do
    opts
    |> Keyword.put(:level, :info)
    |> log(%{
      event: "bot:guild_joined",
      message: "Bot joined the #{guild_name} [#{guild_id}] guild",
      guild_id: guild_id,
      guild_name: guild_name
    })
  end

  @doc false
  def handle_event([:tornium, _event_type, _event], _measurements, _metadata, _opts) do
    :ok
  end

  @spec log(opts :: Keyword.t(), event_data :: map()) :: term()
  defp log(opts, event_data) when is_map(event_data) do
    level = Keyword.get(opts, :level, :debug)
    Logger.log(level, event_data, event_source: :telemetry)
  end
end
