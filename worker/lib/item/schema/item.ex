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

defmodule Tornium.Schema.Item do
  use Ecto.Schema

  @type t :: %__MODULE__{
          tid: integer(),
          name: String.t(),
          description: String.t(),
          item_type: String.t(),
          market_value: integer(),
          circulation: integer()
        }

  @primary_key {:tid, :integer, autogenerate: false}
  schema "item" do
    field(:name, :string)
    field(:description, :string)
    field(:item_type, :string)
    field(:market_value, :integer)
    field(:circulation, :integer)
  end
end
