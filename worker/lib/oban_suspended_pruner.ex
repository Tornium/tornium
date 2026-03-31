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

defmodule Tornium.SuspendedPruner do
  @moduledoc """
  Periodically prune suspended jobs that were not fulfilled.
  """

  @behaviour Oban.Plugin

  use GenServer
  import Ecto.Query

  @impl Oban.Plugin
  def start_link(opts) do
    name = Keyword.get(opts, :name, __MODULE__)

    GenServer.start_link(__MODULE__, opts, name: name)
  end

  @impl Oban.Plugin
  def validate(opts) do
    Oban.Validation.validate_schema(opts,
      conf: :any,
      name: :any,
      interval: :pos_integer,
      max_age: :pos_integer
    )
  end

  @impl GenServer
  def init(opts \\ []) do
    Process.flag(:trap_exit, true)

    state = %{
      conf: Keyword.fetch!(opts, :conf),
      interval: Keyword.get(opts, :interval, 5_000),
      max_age: Keyword.get(opts, :max_age),
      timer: nil
    }

    {:ok, schedule_prune(state)}
  end

  @impl GenServer
  def terminate(_reason, state) do
    if is_reference(state.timer) do
      Process.cancel_timer(state.timer)
    end

    :ok
  end

  @impl GenServer
  def handle_info(:prune, state) do
    if Oban.Peer.leader?(state.conf) do
      Tornium.ObanRepo.transact(state.conf, fn ->
        {:ok, pruned_jobs} = prune(state)

        %{pruned_count: length(pruned_jobs), pruned_jobs: pruned_jobs}
      end)
    else
      {:ok, %{pruned_count: 0, pruned_jobs: []}}
    end

    {:noreply, schedule_prune(state)}
  end

  defp schedule_prune(%{interval: interval} = state) when is_integer(interval) do
    %{state | timer: Process.send_after(self(), :prune, interval)}
  end

  defp prune(%{conf: conf, max_age: max_age} = _state) do
    # Based upon https://github.com/oban-bg/oban/blob/main/lib/oban/engines/basic.ex#L156
    # Modified to prune suspended jobs that were inserted more than `max_age` ago:w

    time = DateTime.add(DateTime.utc_now(), -max_age)

    subquery =
      Oban.Job
      |> select([:id, :queue, :state])
      |> where([j], j.state == "suspended" and j.inserted_at < ^time)
      |> where([j], not is_nil(j.queue))

    query =
      Oban.Job
      |> join(:inner, [j], x in subquery(subquery), on: j.id == x.id)
      |> select([_, x], map(x, [:id, :queue, :state]))

    {_count, pruned} = Tornium.ObanRepo.delete_all(conf, query)

    {:ok, pruned}
  end
end
