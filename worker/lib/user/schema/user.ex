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

defmodule Tornium.Schema.User do
  use Ecto.Schema
  import Ecto.Query

  @type t :: %__MODULE__{
          tid: integer(),
          name: String.t(),
          level: integer(),
          discord_id: integer(),
          battlescore: float(),
          strength: integer(),
          defense: integer(),
          speed: integer(),
          dexterity: integer(),
          faction: Tornium.Schema.Faction.t(),
          faction_aa: boolean(),
          faction_position: Tornium.Schema.FactionPosition.t(),
          status: String.t(),
          last_action: DateTime.t(),
          last_refresh: DateTime.t(),
          last_attacks: DateTime.t(),
          battlescore_update: DateTime.t(),
          security: integer(),
          otp_secret: String.t(),
          otp_backups: [String.t()],
          settings: Tornium.Schema.UserSettings.t() | nil,
          current_elimination_member: Tornium.Schema.EliminationMember.t() | nil
        }

  @primary_key {:tid, :integer, autogenerate: false}
  schema "user" do
    field(:name, :string)
    field(:level, :integer)
    field(:discord_id, :integer)
    # has_one(:personal_stats, Tornium.Schema.PersonalStats)

    field(:battlescore, :float)
    field(:strength, :integer)
    field(:defense, :integer)
    field(:speed, :integer)
    field(:dexterity, :integer)

    belongs_to(:faction, Tornium.Schema.Faction, references: :tid)
    field(:faction_aa, :boolean)
    belongs_to(:faction_position, Tornium.Schema.FactionPosition, references: :pid, type: :binary_id)

    field(:status, :string)
    field(:last_action, :utc_datetime)

    field(:last_refresh, :utc_datetime_usec)
    field(:last_attacks, :utc_datetime_usec)
    field(:battlescore_update, :utc_datetime_usec)

    field(:security, :integer)
    field(:otp_secret, :string)
    field(:otp_backups, {:array, :string})

    belongs_to(:settings, Tornium.Schema.UserSettings, references: :guid, type: :binary_id)

    has_one(:current_elimination_member, Tornium.Schema.EliminationMember, foreign_key: :user_id, references: :tid)
  end

  @doc """
  Join and preload the elimination data for the user for the most recent team they were on.
  """
  @spec preload_elimination_member(query :: Ecto.Query.t()) :: Ecto.Query.t()
  def preload_elimination_member(query) do
    %DateTime{year: year} = DateTime.utc_now()

    query
    |> join(:left, [u], em in assoc(u, :current_elimination_member), on: em.user_id == u.tid)
    |> join(:inner, [u, em], et in assoc(em, :team), on: et.guid == em.team_id)
    |> where([u, em, et], et.year == ^year)
  end
end
