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

defmodule Tornium.Faction.OC.Check.Struct do
  defstruct [:missing_tools, :delayers]

  @type checked_slots :: [Tornium.Schema.OrganizedCrimeSlot.t()]
  @type t :: %Tornium.Faction.OC.Check.Struct{
          missing_tools: checked_slots(),
          delayers: checked_slots()
        }
  @type keys :: :missing_tools | :delayers

  @spec new() :: t()
  def new() do
    %Tornium.Faction.OC.Check.Struct{
      missing_tools: [],
      delayers: []
    }
  end
end
