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

defmodule Tornium.Schema.FactionConfig do
  @moduledoc """
  Faction-specific settings.

  Allows for the toggling of features that could retrieve data using faction AA API keys. If there
  is no config for a faction, the default values will be assumed.

  ## Fields
  - `:guid` - Internal identifier
  - `:faction` - User the settings belong to
  - `:ts_stats_enabled` - Toggle for retrieval of stats of members from TornStats (default: `true`)
  """

  use Ecto.Schema

  @type t :: %__MODULE__{
          guid: Ecto.UUID.t(),
          faction_id: pos_integer(),
          faction: Tornium.Schema.Faction.t(),
          ts_stats_enabled: boolean()
        }

  @primary_key {:guid, Ecto.UUID, autogenerate: true}
  schema "faction_config" do
    belongs_to(:faction, Tornium.Schema.Faction, references: :tid)

    field(:ts_stats_enabled, :boolean)
    # TODO: Move :stats_db_enabled and :stats_db_global from /stats/config to this
    # from the faction schame
  end
end
