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

defmodule Tornium.Faction.ChainMonitor.Discovery do
  @moduledoc """
  Discovery and auto-start of a `ChainMonitor` a faction that is chaining.

  If a faction is chaining and has the feature configured, a `ChainMonitor` should be
  started against that faction. We can determine if a faction is chaining with the 
  `Tornium.Schema.Chain` database table. It can also be manually started by other features.
  """

  # TODO: Implement this
  # This is blocked by adding the chain data to the database
end
