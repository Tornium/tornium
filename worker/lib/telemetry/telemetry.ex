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
  @moduledoc """
  Logging of events from Tornium.

  ## Telemetry Events
  * `[:tornium, :oc_team, :member_removed]`: TBA
    * Measurement: `%{}`
    * Metadata: `%{}`

  * `[:tornium, :bot, :guild_joined]`: Executed when the bot joins a specific Discord server.
    * Measurement: `%{}`
    * Metadata: `%{guild_id: pos_integer, guild_name: String.t}`

  * `[:tornium, :guild, :verify, :config_error]`: Dispatched by `Tornium.Workers.GuildVerify`
    when a server does not have a valid verification configuration to verify its members.
    * Measurement: `%{}`
    * Metadata: `%{guild_id: pos_integer, user_id: nil | pos_integer, error: String.t}`

  * `[:tornium, :guild, :verify, :success]`: Dispatched by `Tornium.Guild.Verify` when
    the Discord server member was successfully verified with some change. This will not be
    dispatched when the member was verified without their nickname and/or roles changing.
    * Measurement: `%{}`
    * Metadata: `%{guild_id: pos_integer, user_id: pos_integer, discord_id: pos_integer, old_nickname: string, new_nickname: string, added_roles: [pos_integer], removed_roles: [pos_integer]}`
  """

  require Logger

  @handler_id "tornium-telemetry-handler"

  @doc """
  Attaches the default Tornium `:telemetry` handler.
  """
  @spec attach_default_logger(opts :: Keyword.t()) :: :ok | {:error, :already_exists}
  def attach_default_logger(opts \\ []) when is_list(opts) do
    events = [
      [:tornium, :oc_team, :member_removed],
      [:tornium, :bot, :guild_joined],
      [:tornium, :guild, :verify, :config_error],
      [:tornium, :guild, :verify, :success]
    ]

    # TODO: Add failed verification to telemetry logs

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
  def handle_event(
        [:tornium, :guild, :verify, :config_error],
        %{} = _measurements,
        %{guild_id: guild_id, user_id: user_id, error: error} = _metadata,
        opts
      )
      when is_nil(user_id) do
    opts
    |> Keyword.put(:level, :info)
    |> log(%{
      event: "guild:verify:config_error",
      message: "Bot failed to verify all users of guild #{guild_id} due to #{error}",
      guild_id: guild_id,
      user_id: nil,
      error: error
    })
  end

  @doc false
  def handle_event(
        [:tornium, :guild, :verify, :config_error],
        %{} = _measurements,
        %{guild_id: guild_id, user_id: user_id, error: error} = _metadata,
        opts
      )
      when not is_nil(user_id) do
    opts
    |> Keyword.put(:level, :info)
    |> log(%{
      event: "guild:verify:config_error",
      message: "Bot failed to verify member #{user_id} of guild #{guild_id} due to #{error}",
      guild_id: guild_id,
      user_id: user_id,
      error: error
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
        opts
      ) do
    opts
    |> Keyword.put(:level, :debug)
    |> log(%{
      event: "guild:verify:success",
      message:
        "Member #{user_id} of guild #{guild_id} was verified with the nick #{old_nickname} -> #{new_nickname}, the removed roles #{removed_roles |> inspect()}, and the added roles #{added_roles |> inspect()}",
      guild_id: guild_id,
      user_id: user_id,
      discord_id: discord_id
    })
  end

  @doc false
  def handle_event([:tornium | _], _measurements, _metadata, _opts) do
    :ok
  end

  @doc false
  def handle_event([:oban, :job, :exception], _measurements, metadata, _opts) do
    metadata |> inspect() |> Logger.info()
  end

  @spec log(opts :: Keyword.t(), event_data :: map()) :: term()
  defp log(opts, event_data) when is_map(event_data) do
    level = Keyword.get(opts, :level, :debug)
    Logger.log(level, event_data, event_source: :telemetry)
  end
end
