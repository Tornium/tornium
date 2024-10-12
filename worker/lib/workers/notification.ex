# Copyright (C) 2021-2023 tiksan
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

defmodule Tornium.Workers.Notification do
  require Logger
  alias Tornium.Repo

  use Oban.Worker,
    max_attempts: 2,
    priority: 5,
    queue: :notifications,
    tags: ["notification"]

  @impl Oban.Worker
  def perform(%Oban.Job{} = job) do
    IO.inspect(job)
    :ok
  end
end
