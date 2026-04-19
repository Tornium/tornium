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

defmodule Tornium.Faction.ChainMonitor.Supervisor do
  @moduledoc """
  Supervisor for the chain monitor.
  """

  use Supervisor

  @doc """
  Start the supervisor for chain monitors.
  """
  @spec start_link(opts :: keyword()) :: term()
  def start_link(opts \\ []) do
    opts =
      opts
      |> Keyword.put_new(:strategy, :one_for_one)

    Supervisor.start_link(__MODULE__, opts, name: __MODULE__)
  end

  @impl true
  def init(opts \\ []) do
    children = [
      {Registry, keys: :unique, name: Tornium.Faction.ChainMonitor.Registry},
      {DynamicSupervisor, name: Tornium.Faction.ChainMonitor.MonitorSupervisor, strategy: :one_for_one},
      Tornium.Faction.ChainMonitor.Discovery
    ]

    Supervisor.init(children, opts)
  end
end
