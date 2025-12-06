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

defmodule Tornium.Schema.EliminationTeam do
  @moduledoc """
  A table defining the teams for each year.
  """

  use Ecto.Schema

  @type t :: %__MODULE__{
          guid: Ecto.UUID.t(),
          year: pos_integer(),
          name: String.t()
        }

  @primary_key {:guid, Ecto.UUID, autogenerate: true}
  schema "elimination_team" do
    field(:year, :integer)
    field(:name, :string)

    has_many(:members, Tornium.Schema.EliminationMember, foreign_key: :team_id)
  end
end
