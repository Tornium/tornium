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

defmodule Tornium.Schema.Faction do
  use Ecto.Schema

  @primary_key {:tid, :integer, autogenerate: false}
  schema "faction" do
    field(:name, :string)
    field(:tag, :string)
    field(:respect, :integer)
    field(:capacity, :integer)
    has_one(:leader_id, Tornium.Schema.User)
    has_one(:coleader_id, Tornium.Schema.User)

    has_one(:guild_id, Tornium.Schema.Server)

    field(:assist_servers, {:array, :integer})

    field(:stats_db_enabled, :boolean)
    field(:stats_db_global, :boolean)

    field(:od_channel, :integer)
    field(:od_data, :map)

    field(:last_members, :utc_datetime_usec)
    field(:last_attacks, :utc_datetime_usec)
  end
end
