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

defmodule Tornium.Schema.UserSettings do
  @moduledoc """
  User-specific settings.

  Allows for the toggling of features that would retrieve data using a user's API key.

  ## Fields
  - `:guid` - Internal identifier
  - `:user` - User the settings belong to
  - `:cpr_enabled` - Toggle for retrieval of the user's CPRs in OCs
  - `:stat_db_enabled` - Toggle for storage of opponent's stats in the stat DB via FF calculations
  - `:od_drug_enabled` - Toggle for retrieval of overdose drug from user's logs
  """

  use Ecto.Schema
  import Ecto.Query
  alias Tornium.Repo

  @type t :: %__MODULE__{
          guid: Ecto.UUID.t(),
          user_id: non_neg_integer(),
          user: Tornium.Schema.User.t(),
          cpr_enabled: boolean(),
          stat_db_enabled: boolean()
        }

  @primary_key {:guid, Ecto.UUID, autogenerate: true}
  schema "user_settings" do
    belongs_to(:user, Tornium.Schema.User, references: :tid)

    field(:cpr_enabled, :boolean)

    field(:stat_db_enabled, :boolean)

    field(:od_drug_enabled, :boolean)
  end

  @doc """
  Check if the user enabled OD drug retrieval from their logs.

  If the user does not have a settings row in the user_settings table, this will default to `false`.
  """
  @spec od_drug?(user_id :: non_neg_integer()) :: boolean()
  def od_drug?(user_id) when is_integer(user_id) do
    od_drug_enabled? =
      __MODULE__
      |> select([s], s.od_drug_enabled)
      |> where([s], s.user_id == ^user_id)
      |> first()
      |> Repo.one()

    od_drug_enabled? || false
  end
end
