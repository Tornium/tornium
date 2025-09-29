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

defmodule Tornium.Schema.UserSettings do
  @moduledoc """
  User-specific settings.

  Allows for the toggling of features that would retrieve data using a user's API key.

  ## Fields
  - `:guid` - Internal identifier
  - `:user` - User the settings belong to
  - `:cpr_enabled` - Toggle for retrieval of the user's CPRs in OCs
  """

  use Ecto.Schema

  @type t :: %__MODULE__{
          guid: Ecto.UUID.t(),
          user_id: integer(),
          user: Tornium.Schema.User.t(),
          cpr_enabled: boolean()
        }

  @primary_key {:guid, Ecto.UUID, autogenerate: true}
  schema "user_settings" do
    belongs_to(:user, Tornium.Schema.User, references: :tid)

    field(:cpr_enabled, :boolean)
  end
end
