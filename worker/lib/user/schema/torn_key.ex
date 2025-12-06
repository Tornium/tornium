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

defmodule Tornium.Schema.TornKey do
  use Ecto.Schema

  @type access_levels() :: :public | :minimal | :limited | :full

  @type t :: %__MODULE__{
          guid: Ecto.UUID.t(),
          api_key: String.t(),
          user_id: pos_integer(),
          user: Tornium.Schema.User.t(),
          default: boolean(),
          disabled: boolean(),
          paused: boolean(),
          access_level: access_levels()
        }

  @primary_key {:guid, Ecto.UUID, autogenerate: true}
  schema "tornkey" do
    field(:api_key, :string)
    belongs_to(:user, Tornium.Schema.User, references: :tid)
    field(:default, :boolean)
    field(:disabled, :boolean)
    field(:paused, :boolean)
    field(:access_level, Ecto.Enum, values: [public: 1, minimal: 2, limited: 3, full: 4])
  end
end
