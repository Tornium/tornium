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
  @moduledoc """
  Schema representing a Torn user.
  """

  use Ecto.Schema
  import Ecto.Query
  alias Tornium.Repo

  @type t :: %__MODULE__{
          tid: pos_integer(),
          name: String.t() | nil,
          level: 0..100 | nil,
          discord_id: non_neg_integer() | nil,
          battlescore: float() | nil,
          strength: pos_integer() | nil,
          defense: pos_integer() | nil,
          speed: pos_integer() | nil,
          dexterity: pos_integer() | nil,
          faction_id: pos_integer() | nil,
          faction: Tornium.Schema.Faction.t() | nil,
          faction_aa: boolean(),
          faction_position_id: Ecto.UUID.t() | nil,
          faction_position: Tornium.Schema.FactionPosition.t() | nil,
          status: String.t() | nil,
          last_action: DateTime.t() | nil,
          last_refresh: DateTime.t() | nil,
          last_attacks: DateTime.t() | nil,
          battlescore_update: DateTime.t() | nil,
          security: 0..1 | nil,
          otp_secret: String.t() | nil,
          otp_backups: [String.t()],
          settings_id: Ecto.UUID.t() | nil,
          settings: Tornium.Schema.UserSettings.t() | nil
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

    # TODO: Convert `:security` into an Ecto Enum
    field(:security, :integer)
    field(:otp_secret, :string)
    field(:otp_backups, {:array, :string})

    belongs_to(:settings, Tornium.Schema.UserSettings, references: :guid, type: :binary_id)
  end

  @type ensure_exists_user :: {user_id :: pos_integer(), user_name :: String.t() | nil}

  @doc """
  Bulk upsert users' IDs and names to ensure that exist in the database.

  This is to prevent failures in other inserts/upserts that depend upon the user table as a foreign key.
  **NOTE**: Do not rely upon this function to update user names.
  """
  @spec ensure_exists(users :: [ensure_exists_user()]) :: :ok
  def ensure_exists(users) when is_list(users) do
    mapped_users =
      users
      |> Enum.uniq_by(fn {user_id, _user_name} when is_integer(user_id) -> user_id end)
      |> Enum.map(fn {user_id, user_name} when is_integer(user_id) and (is_binary(user_name) or is_nil(user_name)) ->
        %{tid: user_id, name: user_name}
      end)

    Repo.insert_all(
      __MODULE__,
      mapped_users,
      on_conflict: :nothing,
      conflict_target: :tid
    )

    :ok
  end
end
