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

defmodule Tornium.Schema.EliminationRecord do
  @moduledoc """
  The records of an elimination member's performance at a point in time.
  """

  use Ecto.Schema

  @type t :: %__MODULE__{
          guid: Ecto.UUID.t(),
          member_id: Ecto.UUID.t(),
          member: Tornium.Schema.EliminationMember.t(),
          score: pos_integer(),
          attacks: pos_integer()
        }

  @primary_key {:guid, Ecto.UUID, autogenerate: true}
  schema "elimination_member" do
    belongs_to(:member, Tornium.Schema.EliminationMember, references: :guid)

    field(:score, :integer)
    field(:attacks, :integer)
  end
end
