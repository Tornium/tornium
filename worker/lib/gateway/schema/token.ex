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

defmodule Tornium.Schema.GatewayToken do
  @moduledoc """
  A short-lived token from the Flask API for use connecting to the Elixir SSE gateway.
  """

  use Ecto.Schema

  @type t :: %__MODULE__{
          guid: Ecto.UUID.t(),
          user_id: pos_integer(),
          user: Tornium.Schema.User.t(),
          token: String.t(),
          created_at: DateTime.t(),
          created_ip: term(),
          expires_at: DateTime.t()
        }

  @primary_key {:guid, Ecto.UUID, autogenerate: true}
  schema "gateway_token" do
    belongs_to(:user, Tornium.Schema.User, references: :tid)
    field(:token, :string)

    field(:created_at, :utc_datetime)
    field(:created_ip, EctoNetwork.INET)
    field(:expires_at, :utc_datetime)
  end
end
