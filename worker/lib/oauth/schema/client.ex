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

defmodule Tornium.Schema.OAuthClient do
  @moduledoc """
  OAuth 2.0 client.

  An OAuth client using client credentials grant can have a multiple resource consents granting
  permissions for the application utilizing the client to access some resources. As client
  credential grant requires confidential clients, only a single application would be using the
  OAuth client.
  """

  use Ecto.Schema

  @type t :: %__MODULE__{
          client_id: String.t(),
          client_secret: String.t() | nil,
          client_id_issued_at: DateTime.t(),
          client_secret_expires_at: DateTime.t() | nil,
          client_metadata: map(),
          deleted_at: DateTime.t() | nil,
          user_id: integer(),
          user: Tornium.Schema.User.t(),
          consents: [Tornium.Schema.OAuthClientResourceConsent.t()]
        }

  @primary_key {:client_id, :string, autogenerate: false}
  schema "oauthclient" do
    field(:client_secret, :string)
    field(:client_id_issued_at, :utc_datetime)
    field(:client_secret_expires_at, :utc_datetime)
    field(:client_metadata, :map)

    field(:deleted_at, :utc_datetime)

    belongs_to(:user, Tornium.Schema.User, references: :tid)

    has_many(:consents, Tornium.Schema.OAuthClientResourceConsent, foreign_key: :client_id, references: :client_id)
  end
end
