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

defmodule Tornium.Schema.OAuthToken do
  @moduledoc """
  OAuth 2.0 access/refresh token.
  """
  use Ecto.Schema

  @type t :: %__MODULE__{
          id: integer(),
          client: Tornium.Schema.OAuthClient.t(),
          token_type: String.t(),
          access_token: String.t(),
          refresh_token: String.t() | nil,
          scope: String.t(),
          issued_at: DateTime.t(),
          access_token_revoked_at: DateTime.t() | nil,
          refresh_token_revoked_at: DateTime.t() | nil,
          expires_in: integer(),
          user: Tornium.Schema.User.t()
        }

  @primary_key {:id, :id, autogenerate: true}
  schema "oauthtoken" do
    belongs_to(:client, Tornium.Schema.OAuthClient, references: :client_id, type: :string)
    field(:token_type, :string)
    field(:access_token, :string)
    field(:refresh_token, :string)
    field(:scope, :string)
    field(:issued_at, :utc_datetime)
    field(:access_token_revoked_at, :utc_datetime)
    field(:refresh_token_revoked_at, :utc_datetime)
    field(:expires_in, :integer)

    belongs_to(:user, Tornium.Schema.User, references: :tid)
  end
end
