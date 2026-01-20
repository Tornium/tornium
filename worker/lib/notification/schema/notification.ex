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

defmodule Tornium.Schema.Notification do
  @moduledoc """
  Notification for a specific trigger against a specific resource ID with customized parameters.
  """

  use Ecto.Schema

  @type t :: %__MODULE__{
          nid: Ecto.UUID.t(),
          trigger_id: Ecto.UUID.t(),
          trigger: Tornium.Schema.Trigger.t(),
          user_id: pos_integer(),
          user: Tornium.Schema.User.t(),
          enabled: boolean(),
          server_id: pos_integer() | nil,
          server: Tornium.Schema.Server.t() | nil,
          channel_id: pos_integer() | nil,
          message_id: pos_integer() | nil,
          resource_id: integer() | nil,
          one_shot: boolean(),
          parameters: %{String.t() => term()},
          error: String.t() | nil,
          previous_state: %{String.t() => term()}
        }

  @primary_key {:nid, Ecto.UUID, autogenerate: true}
  schema "notification" do
    belongs_to(:trigger, Tornium.Schema.Trigger, references: :tid, type: Ecto.UUID)
    belongs_to(:user, Tornium.Schema.User, references: :tid)
    field(:enabled, :boolean)

    belongs_to(:server, Tornium.Schema.Server, references: :sid)
    field(:channel_id, :integer)
    field(:message_id, :integer)

    field(:resource_id, :integer)
    field(:one_shot, :boolean)
    field(:parameters, :map)

    field(:error, :string)
    field(:previous_state, :map)
  end

  # TODO: Add docs and return type
  @doc """
  """
  @spec disable(notifications :: [Ecto.UUID.t()], reason :: String.t()) :: :ok
  def disable([], _reason) do
    :ok
  end

  def disable(notifications, reason) when is_list(notifications) and is_binary(reason) do
    # TODO: Implement this end
    :ok
  end
end
