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

defmodule Tornium.Schema.Trigger do
  # TODO: Add a summary for the moduledoc
  @moduledoc """
  TODO

  If there is no `:next_execution` value, the notification trigger will be executed immediately to determine
  when the notification trigger should next be triggered. Otherwise, the notification trigger will be executed
  at the next `:next_execution` value as determined by `:cron` during the previous execution.
  """

  use Ecto.Schema

  @type t :: %__MODULE__{
          tid: Ecto.UUID.t(),
          name: String.t(),
          description: String.t(),
          owner_id: pos_integer(),
          owner: Tornium.Schema.User.t(),
          cron: String.t(),
          next_execution: DateTime.t() | nil,
          resource: :user | :faction | :company | :torn | :faction_v2,
          selections: [String.t()],
          code: String.t(),
          # TODO: Determine the right hand side type (it may be integer() | string.t())
          parameters: %{String.t() => term()},
          message_type: :update | :send,
          message_template: String.t(),
          restricted_data: boolean(),
          official: boolean()
        }

  @primary_key {:tid, Ecto.UUID, autogenerate: true}
  schema "notification_trigger" do
    field(:name, :string)
    field(:description, :string)
    belongs_to(:owner, Tornium.Schema.User, references: :tid)

    field(:cron, :string)
    field(:next_execution, :utc_datetime)

    field(:resource, Ecto.Enum, values: [:user, :faction, :company, :torn, :faction_v2])
    field(:selections, {:array, :string})
    field(:code, :string)
    field(:parameters, :map)

    field(:message_type, Ecto.Enum, values: [:update, :send])
    field(:message_template, :string)

    field(:restricted_data, :boolean)
    field(:official, :boolean)
  end
end
