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

  test "validate to_list/1 with valid values" do
    vm = Tornium.Notification.Lua.setup_vm()

    assert {[["1", "2", "3"]], _} = Lua.eval!(vm, ~LUA[return tornium.to_list("1,2,3")]c)
    assert {[["1", "2", "3"]], _} = Lua.eval!(vm, ~LUA[return tornium.to_list("1, 2, 3")]c)
    assert {[[]], _} = Lua.eval!(vm, ~LUA[return tornium.to_list("")]c)
  end

  test "validate to_list/2 with valid values and types" do
    vm = Tornium.Notification.Lua.setup_vm()

    assert {[[1, 2, 3]], _} = Lua.eval!(vm, ~LUA[return tornium.to_list("1,2,3", "integer")]c)
    assert {[[1, 2, 3]], _} = Lua.eval!(vm, ~LUA[return tornium.to_list("1, 2, 3", "integer")]c)
    assert {[[]], _} = Lua.eval!(vm, ~LUA[return tornium.to_list("", "integer")]c)

    assert {[["1", "2", "3"]], _} = Lua.eval!(vm, ~LUA[return tornium.to_list("1,2,3", "string")]c)
    assert {[["1", "2", "3"]], _} = Lua.eval!(vm, ~LUA[return tornium.to_list("1, 2, 3", "string")]c)
    assert {[[]], _} = Lua.eval!(vm, ~LUA[return tornium.to_list("", "string")]c)
  end

  test "validate to_list/2 with invalid values/types" do
    vm = Tornium.Notification.Lua.setup_vm()

    assert {[[1, 2, 3]], _} = Lua.eval!(vm, ~LUA[return tornium.to_list("foo, bar, 1, 2, 3, foo, bar", "integer")]c)
    assert {[[]], _} = Lua.eval!(vm, ~LUA[return tornium.to_list("foo, bar, 1, 2, 3, foo, bar", "boolean")]c)
  end

  test "validate to_list_strict/2 with valid values" do
    vm = Tornium.Notification.Lua.setup_vm()

    assert {[[1, 2, 3]], _} = Lua.eval!(vm, ~LUA[return tornium.to_list_strict("1,2,3", "integer")]c)
    assert {[[1, 2, 3]], _} = Lua.eval!(vm, ~LUA[return tornium.to_list_strict("1, 2, 3", "integer")]c)
    assert {[[]], _} = Lua.eval!(vm, ~LUA[return tornium.to_list_strict("", "integer")]c)

    assert {[["1", "2", "3"]], _} = Lua.eval!(vm, ~LUA[return tornium.to_list_strict("1,2,3", "string")]c)
    assert {[["1", "2", "3"]], _} = Lua.eval!(vm, ~LUA[return tornium.to_list_strict("1, 2, 3", "string")]c)
    assert {[[]], _} = Lua.eval!(vm, ~LUA[return tornium.to_list_strict("", "string")]c)
  end

  test "validate to_list_strict/2 with invalid values/types" do
    vm = Tornium.Notification.Lua.setup_vm()

    assert_raise Lua.RuntimeException, "Cannot convert foo to integer", fn ->
      Lua.eval!(vm, ~LUA[return tornium.to_list_strict("foo, bar, 1, 2, 3, foo, bar", "integer")]c)
    end

    assert_raise Lua.RuntimeException, "Cannot convert 5 to boolean", fn ->
      Lua.eval!(vm, ~LUA[return tornium.to_list_strict("5, foo, bar, 1, 2, 3, foo, bar", "boolean")]c)
    end
  end
end
