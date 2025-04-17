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

defmodule Tornium.Schema.ServerOCRangeConfig do
  use Ecto.Schema

  @type t :: %__MODULE__{
          guid: Ecto.UUID.t(),
          server_oc_config_id: Ecto.UUID.t(),
          server_oc_config: Tornium.Schema.ServerOCConfig.t(),
          oc_name: String.t(),
          minimum: integer(),
          maximum: integer()
        }

  @primary_key {:guid, Ecto.UUID, autogenerate: true}
  schema "server_oc_range_config" do
    belongs_to(:server_oc_config, Tornium.Schema.ServerOCConfig, references: :guid, type: :binary_id)
    field(:oc_name, :string)
    field(:minimum, :integer)
    field(:maximum, :integer)
  end
end
