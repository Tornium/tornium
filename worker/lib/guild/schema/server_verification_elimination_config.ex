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

defmodule Tornium.Schema.ServerVerificationEliminationConfig do
  @moduledoc """
  Configuration in a server for an elimination team.
  """

  use Ecto.Schema

  @type t :: %__MODULE__{
          guid: Ecto.UUID.t(),
          server_id: pos_integer(),
          server: Tornium.Schema.Server.t(),
          team_id: Ecto.UUID.t(),
          team: Tornium.Schema.EliminationTeam.t(),
          roles: [Tornium.Discord.role()]
        }

  @primary_key {:guid, Ecto.UUID, autogenerate: true}
  schema "server_verification_elimination_config" do
    belongs_to(:server, Tornium.Schema.Server, references: :sid)
    belongs_to(:team, Tornium.Schema.EliminationTeam, references: :guid)

    field(:roles, {:array, :integer})
  end
end
