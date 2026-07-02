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

defmodule Tornium.Schema.Stat do
  @moduledoc """
  Schema representing a user's stat entry in the stat database.
  """

  use Ecto.Schema

  @type t :: %__MODULE__{
          id: integer(),
          tid_id: pos_integer(),
          tid: Tornium.Schema.User.t(),
          battlescore: float(),
          time_added: DateTime.t(),
          added_group: non_neg_integer()
        }

  @primary_key {:id, :id, autogenerate: true}
  schema "stat" do
    belongs_to(:tid, Tornium.Schema.User, references: :tid)
    field(:battlescore, :float)
    field(:time_added, :utc_datetime)
    field(:added_group, :integer)
  end
end
