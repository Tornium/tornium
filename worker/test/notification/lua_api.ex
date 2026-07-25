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

defmodule Tornium.Test.Notification.Lua.API do
  @moduledoc false

  use Tornium.RepoCase
  import Lua, only: [sigil_LUA: 2]

  test "validate to_boolean/1 with valid values" do
    vm = Tornium.Notification.Lua.setup_vm()

    assert {[false], _} = Lua.eval!(vm, ~LUA[return tornium.to_boolean(0)]c)
    assert {[false], _} = Lua.eval!(vm, ~LUA[return tornium.to_boolean("0")]c)
    assert {[false], _} = Lua.eval!(vm, ~LUA[return tornium.to_boolean("false")]c)
    assert {[false], _} = Lua.eval!(vm, ~LUA[return tornium.to_boolean("False")]c)
    assert {[true], _} = Lua.eval!(vm, ~LUA[return tornium.to_boolean(1)]c)
    assert {[true], _} = Lua.eval!(vm, ~LUA[return tornium.to_boolean("1")]c)
    assert {[true], _} = Lua.eval!(vm, ~LUA[return tornium.to_boolean("true")]c)
    assert {[true], _} = Lua.eval!(vm, ~LUA[return tornium.to_boolean("True")]c)
  end
end
