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

defmodule Tornium.Schema.Notification do
  use Ecto.Schema

  @type t :: %__MODULE__{
          nid: Ecto.UUID.t(),
          trigger: Tornium.Schema.Trigger.t(),
          user: Tornium.Schema.User.t(),
          enabled: boolean(),
          server: Tornium.Schema.Server.t(),
          channel_id: integer(),
          resource_id: integer(),
          one_shot: boolean(),
          parameters: map(),
          next_execution: DateTime.t(),
          message_id: integer(),
          error: String.t() | nil,
          previous_state: map()
        }

  @primary_key {:nid, Ecto.UUID, autogenerate: true}
  schema "notification" do
    belongs_to(:trigger, Tornium.Schema.Trigger, references: :tid)
    belongs_to(:user, Tornium.Schema.User, references: :tid)
    field(:enabled, :boolean)

    belongs_to(:server, Tornium.Schema.Server, references: :sid)
    field(:channel_id, :integer)

    field(:resource_id, :integer)
    field(:one_shot, :boolean)
    field(:parameters, :map)

    field(:next_execution, :utc_datetime)
    field(:message_id, :integer)

    field(:error, :string)
    field(:previous_state, :map)
  end
end
