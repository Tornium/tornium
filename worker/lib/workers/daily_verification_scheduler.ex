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

defmodule Tornium.Workers.DailyVerificationScheduler do
  @moduledoc """
  Verify all members of all servers with `:auto_verify_enabled` in chunks.
  """

  alias Tornium.Repo
  import Ecto.Query

  use Oban.Worker,
    max_attempts: 3,
    priority: 0,
    queue: :scheduler,
    tags: ["scheduler"],
    unique: [
      period: :infinity,
      fields: [:worker],
      states: :incomplete
    ]

  @schedule_in_delay 30

  @impl Oban.Worker
  def perform(%Oban.Job{scheduled_at: %DateTime{} = scheduled_at} = _job) do
    current_guild_slot =
      scheduled_at
      |> DateTime.to_unix(:second)
      |> rem(86_400)
      |> div(900)

    Tornium.Schema.Server
    |> where([s], s.verify_enabled == true and s.auto_verify_enabled == true)
    |> where([s], fragment("? % 96", s.sid) == ^current_guild_slot)
    |> Repo.all()
    |> Enum.reduce(0, fn guild, schedule_in_acc ->
      Tornium.Workers.GuildVerification.schedule(guild, schedule_in: schedule_in_acc)

      schedule_in_acc + @schedule_in_delay
    end)

    :ok
  end

  @impl Oban.Worker
  def timeout(%Oban.Job{} = _job) do
    :timer.minutes(5)
  end
end
