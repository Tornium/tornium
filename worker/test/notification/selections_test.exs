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

defmodule Tornium.Test.Notification.Selections do
  use Tornium.RepoCase, async: true

  test "test_find_modules" do
    invalid_resource = Tornium.Notification.Selections.find_module("test123")
    assert map_size(invalid_resource) == 0

    faction_resource = Tornium.Notification.Selections.find_module("faction")
    assert map_size(faction_resource) != 0
    assert not is_nil(Map.get(faction_resource, {"faction", "attacks"}))
    assert is_nil(Map.get(faction_resource, {"faction", "foo_bar"}))

    faction_id_resource = Tornium.Notification.Selections.find_module("faction/{id}")
    assert map_size(faction_id_resource) != 0
    assert not is_nil(Map.get(faction_id_resource, {"faction/{id}", "basic"}))
    assert is_nil(Map.get(faction_id_resource, {"faction/{id}", "foo_bar"}))
  end

  test "test_find_modules_selections" do
    invalid_resource = Tornium.Notification.Selections.find_module("test123", "test123")
    assert map_size(invalid_resource) == 0

    faction_resource = Tornium.Notification.Selections.find_module("faction", "attacks")
    assert map_size(faction_resource) == 1
    assert Map.get(faction_resource, {"faction", "attacks"}) == Torngen.Client.Path.Faction.Attacks

    faction_id_resource = Tornium.Notification.Selections.find_module("faction/{id}", "basic")
    assert map_size(faction_id_resource) == 1
    assert Map.get(faction_id_resource, {"faction/{id}", "basic"}) == Torngen.Client.Path.Faction.Id.Basic
  end
end
