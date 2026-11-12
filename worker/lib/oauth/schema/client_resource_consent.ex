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

defmodule Tornium.Schema.OAuthClientResourceConsent do
  @moduledoc """
  Consent for a resource to be accessed by an application's OAuth client.
  """

  use Ecto.Schema

  @type t :: %__MODULE__{
          guid: Ecto.UUID.t(),
          client_id: String.t(),
          client: Tornium.Schema.OAuthClient.t(),
          scope: String.t(),
          faction_id: pos_integer() | nil,
          faction: Tornium.Schema.Faction.t() | nil,
          server_id: pos_integer() | nil,
          server: Tornium.Schema.Server.t() | nil,
          consented_by_id: pos_integer(),
          consented_by: Tornium.Schema.User.t(),
          consented_at: DateTime.t(),
          revoked_by_id: pos_integer() | nil,
          revoked_by: Tornium.Schema.User.t() | nil,
          revoked_at: DateTime.t() | nil
        }

  @primary_key false
  schema "oauth_client_resource_consent" do
    field(:guid, Ecto.UUID, primary_key: true)

    belongs_to(:client, Tornium.Schema.OAuthClient, references: :client_id)
    field(:scope, :string)

    belongs_to(:faction, Tornium.Schema.Faction, references: :tid)
    belongs_to(:server, Tornium.Schema.Server, references: :sid)

    belongs_to(:consented_by, Tornium.Schema.User, references: :tid)
    field(:consented_at, :utc_datetime)
    belongs_to(:revoked_by, Tornium.Schema.User, references: :tid)
    field(:revoked_at, :utc_datetime)
  end
end
