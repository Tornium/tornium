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
  Update a specific server's data.
  """

  import Ecto.Query
  alias Tornium.Repo

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
  def perform(%Oban.Job{args: %{"guild_id" => guild_id} = _args} = _job) do
    %Nostrum.Struct.Guild{name: guild_name, owner_id: guild_owner_id, roles: guild_roles} =
      Nostrum.Api.Guild.get(guild_id)

    Tornium.Schema.Server.new(guild_id, guild_name)

    guild_admins_discord_ids =
      guild_id
      |> Tornium.Guild.fetch_admins(guild_roles)
      |> List.insert_at(0, guild_owner_id)
      |> Enum.uniq()

    guild_admins =
      Tornium.Schema.User
      |> where([u], u.discord_id in ^guild_admins_discord_ids)
      |> select([u], u.tid)
      |> Repo.all()

    Tornium.Schema.Server
    |> update([s], set: [admins: ^guild_admins])
    |> where([s], s.sid == ^guild_id)
    |> Repo.update_all([])

    :ok
  end
end
