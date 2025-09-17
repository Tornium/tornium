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

defmodule Tornium.Test.Faction.Overdose do
  use Tornium.RepoCase, async: true
  alias Tornium.Faction.Overdose
  alias Torngen.Client.Schema.FactionContributor

  doctest Tornium.Faction.Overdose, only: [{:counts, 1}], import: true

  test "test_counts" do
    counts =
      Overdose.counts([
        %FactionContributor{in_faction: true, id: 1, value: 10},
        %FactionContributor{in_faction: false, id: 2, value: 2},
        %FactionContributor{in_faction: true, id: 3, value: 0},
        %FactionContributor{in_faction: false, id: 4, value: 76},
        %FactionContributor{in_faction: true, id: 5, value: 1}
      ])

    assert map_size(counts) == 3
    assert Map.get(counts, 1) == 10
    assert is_nil(Map.get(counts, 2))
    assert Map.get(counts, 3) == 0
    assert is_nil(Map.get(counts, 4))
    assert Map.get(counts, 5) == 1
  end
end
