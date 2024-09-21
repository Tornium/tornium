# Copyright (C) 2021-2023 tiksan
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

defmodule Tornium.Test.User.Key do
  use Tornium.RepoCase

  test "test_get_user_no_key" do
    pid = ExUnit.Callbacks.start_link_supervised!(Tornium.User.KeyStore)
    assert is_nil(Tornium.User.Key.get_by_user(%Tornium.Schema.User{tid: 1, name: "Chedburn"}, pid))
    Agent.stop(pid)
  end

  test "test_get_user_single_key_uncached" do
    pid = ExUnit.Callbacks.start_link_supervised!(Tornium.User.KeyStore)

    {:ok, user} =
      %Tornium.Schema.User{
        tid: 1,
        name: "Chedburn",
        level: 15
      }
      |> Repo.insert()

    {:ok, key} =
      %Tornium.Schema.TornKey{
        api_key: "asdf1234asdf1234",
        user_id: 1,
        default: true,
        paused: false,
        disabled: false,
        access_level: 3
      }
      |> Repo.insert()

    assert Tornium.User.Key.get_by_user(user, pid).api_key == key.api_key
    Agent.stop(pid)
  end

  test "test_get_user_single_key_cached" do
    pid = ExUnit.Callbacks.start_link_supervised!(Tornium.User.KeyStore)

    {:ok, user} =
      %Tornium.Schema.User{
        tid: 1,
        name: "Chedburn",
        level: 15
      }
      |> Repo.insert()

    {:ok, key} =
      %Tornium.Schema.TornKey{
        api_key: "asdf1234asdf1234",
        user_id: 1,
        default: true,
        paused: false,
        disabled: false,
        access_level: 3
      }
      |> Repo.insert()

    _ = Tornium.User.Key.get_by_user(user, pid)
    assert Tornium.User.Key.get_by_user(user, pid).api_key == key.api_key
    Agent.stop(pid)
  end

  test "test_get_user_multiple_keys" do
    pid = ExUnit.Callbacks.start_link_supervised!(Tornium.User.KeyStore)

    {:ok, user} =
      %Tornium.Schema.User{
        tid: 1,
        name: "Chedburn",
        level: 15
      }
      |> Repo.insert()

    {:ok, _key1} =
      %Tornium.Schema.TornKey{
        api_key: "qwerty1234567890",
        user_id: 1,
        default: false,
        paused: false,
        disabled: false,
        access_level: 3
      }
      |> Repo.insert()

    {:ok, key2} =
      %Tornium.Schema.TornKey{
        api_key: "asdf1234asdf1234",
        user_id: 1,
        default: true,
        paused: false,
        disabled: false,
        access_level: 3
      }
      |> Repo.insert()

    assert Tornium.User.Key.get_by_user(user, pid).api_key == key2.api_key
    Agent.stop(pid)
  end
end
