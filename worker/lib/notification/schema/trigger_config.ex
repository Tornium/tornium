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

defmodule Tornium.Schema.TriggerConfig do
  use Ecto.Schema

  @type t :: %__MODULE__{
          tc_id: Ecto.UUID.t(),
          trigger: Tornium.Schema.Trigger.t(),
          user: Tornium.Schema.User.t(),
          resource_id: integer(),
          one_shot: boolean(),
          cron: String.t(),
          next_execution: DateTime.t(),
          error: String.t() | nil,
          previous_state: Map
        }

  @primary_key {:tc_id, Ecto.UUID, autogenerate: true}
  schema "notification_trigger_config" do
    belongs_to(:trigger, Tornium.Schema.Trigger, references: :tid)
    belongs_to(:user, Tornium.Schema.User, references: :tid)

    field(:resource_id, :integer)
    field(:one_shot, :boolean)

    field(:cron, :string)
    field(:next_execution, :utc_datetime)

    field(:error, :string)
    field(:previous_state, :map)
  end
end
