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

defmodule Tornium.Workers.ServerRefresh do
  @moduledoc """
  Update a specfic server's data.
  """

  use Oban.Worker,
    max_attempts: 3,
    priority: 0,
    queue: :guild_processing,
    tags: ["guild"],
    unique: [
      period: :infinity,
      fields: [:worker, :args],
      keys: [:guild_id],
      states: :incomplete
    ]

  @impl Oban.Worker
  def perform(%Oban.Job{args: %{"guild_id" => _guild_id} = _args} = _job) do
    # TODO: Implement this

    :ok
  end
end
