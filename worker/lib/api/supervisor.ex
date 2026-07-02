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

defmodule Tornium.API.Supervisor do
  @moduledoc """
  Supervisor for the sharded API response stores.
  """

  @shards Application.compile_env(:tornium, :api_shards, 2)

  use Supervisor

  @spec start_link(opts :: keyword()) :: Supervisor.on_start()
  def start_link(opts \\ []) do
    Supervisor.start_link(__MODULE__, opts, name: __MODULE__)
  end

  @impl true
  def init(_opts \\ []) do
    children = [
      {Horde.Registry, name: Tornium.API.Registry, keys: :unique, members: :auto},
      {Horde.DynamicSupervisor, name: Tornium.API.ShardSupervisor, strategy: :one_for_one, members: :auto},
      Supervisor.child_spec({Task, &start_shards/0}, restart: :transient)
    ]

    Supervisor.init(children, strategy: :rest_for_one)
  end

  defp start_shards() do
    # As we can't start children for a DynamicSupervisor (or in this case a Horde.DynamicSupervisor)
    # until the parent supervisor's init has finished, we can create a task that does so and attach
    # it to the parent supervisor. This also ensures that the shards are recreated in the
    # Horde.DynamicSupervisor crashes.
    #
    # See https://github.com/slashdotdash/til/blob/master/elixir/dynamic-supervisor-start-children.md

    for shard <- 0..(@shards - 1) do
      child = Horde.DynamicSupervisor.start_child(Tornium.API.ShardSupervisor, {Tornium.API.Store, shard})

      case child do
        {:ok, _} ->
          nil

        {:error, {:already_started, _}} ->
          nil
      end
    end
  end
end
