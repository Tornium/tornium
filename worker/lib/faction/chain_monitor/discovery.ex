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

defmodule Tornium.Faction.ChainMonitor.Discovery do
  @moduledoc """
  Discovery and auto-start of a `ChainMonitor` for a chain of a faction.

  If a faction is chaining and has the feature configured, a `ChainMonitor` should be
  started against that faction's chain. We can determine if a faction is chaining with the 
  `Tornium.Schema.Chain` database table. It can also be manually started by other features.
  """

  @discovery_interval 30_000

  use GenServer
  import Ecto.Query
  alias Tornium.Repo

  @doc """
  Start the `ChainMonitor` discovery GenServer.

  ## Options
    * `:discovery_interval` - The interval in which chain discovery is run in
      milliseconds (default: `30_000`)
  """
  def start_link(opts \\ []) do
    # We want this GenServer to be globally registered to avoid multiple discovery GenServers
    # attempting to spawn the same chain's `ChainMonitor`.
    {name, opts} = Keyword.pop(opts, :name, {:global, __MODULE__})

    case GenServer.start_link(__MODULE__, opts, name: name) do
      {:ok, pid} -> {:ok, pid}
      {:error, {:already_started, _pid}} -> :ignore
    end
  end

  @impl true
  def init(opts \\ []) do
    state = %{
      interval: Keyword.get(opts, :discovery_interval, @discovery_interval),
      monitor_starter: Keyword.get(opts, :monitor_starter, &start_monitor/1)
    }

    schedule_discovery(state.interval)
    {:ok, state}
  end

  @impl true
  def handle_info(:discover, %{interval: interval, monitor_starter: monitor_starter} = state) do
    Enum.each(chaining_faction_ids(), monitor_starter)

    schedule_discovery(interval)
    {:noreply, state}
  end

  @doc false
  @spec chaining_faction_ids() :: [{faction_id :: pos_integer(), chain_id :: pos_integer()}]
  def chaining_faction_ids() do
    Tornium.Schema.TornKey
    |> where([k], k.default == true and k.disabled == false and k.paused == false and k.access_level >= :limited)
    |> join(:inner, [k], u in assoc(k, :user), on: k.user_id == u.tid)
    |> where([k, u], not is_nil(u.faction_id) and not is_nil(u.faction_position_id) and u.faction_aa == true)
    |> join(:inner, [k, u], f in assoc(u, :faction), on: u.faction_id == f.tid)
    |> where([k, u, f], not is_nil(f.guild_id))
    |> join(:inner, [k, u, f], c in assoc(f, :chains), on: f.tid == c.faction_id)
    |> order_by([k, u, f, c], desc: c.start_timestamp, desc: f.tid)
    |> where([k, u, f, c], is_nil(c.end_timestamp))
    |> join(:inner, [k, u, f, c], s in assoc(f, :guild), on: f.guild_id == s.sid)
    |> where([k, u, f, c, s], f.tid in s.factions)
    |> join(:inner, [k, u, f, c, s], sac in assoc(s, :attack_configs), on: s.sid == sac.server_id)
    |> where(
      [k, u, f, c, s, sac],
      sac.faction_id == f.tid and sac.chain_alert_channel != 0 and not is_nil(sac.chain_alert_channel)
    )
    |> distinct([k, u, f, c, s, sac], f.tid)
    |> select([k, u, f, c, s, sac], {f.tid, c.chain_id})
    |> Repo.all()
  end

  @spec schedule_discovery(discovery_interval :: pos_integer()) :: reference()
  defp schedule_discovery(discovery_interval) when is_integer(discovery_interval) do
    Process.send_after(self(), :discover, discovery_interval)
  end

  @spec start_monitor({faction_id :: pos_integer(), chain_id :: pos_integer()}) :: DynamicSupervisor.on_start_child()
  defp start_monitor({faction_id, chain_id}) when is_integer(faction_id) and is_integer(chain_id) do
    Horde.DynamicSupervisor.start_child(
      Tornium.Faction.ChainMonitor.MonitorSupervisor,
      {Tornium.Faction.ChainMonitor, [faction_id: faction_id, chain_id: chain_id]}
    )
  end
end
