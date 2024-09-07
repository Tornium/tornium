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

defmodule Tornium.Test.Guild do
  use Tornium.RepoCase

  test "test_get_admin_keys_invalid" do
    assert Kernel.length(Tornium.Guild.get_admin_keys(0)) == 0
  end

  test "test_get_admin_keys_none" do
    assert Kernel.length(
             Tornium.Guild.get_admin_keys(%Tornium.Schema.Server{
               sid: 1,
               name: "Test server",
               admins: []
             })
           ) == 0
  end

  test "test_get_admin_keys_single" do
    server =
      %Tornium.Schema.Server{
        sid: 1,
        name: "Test server 1",
        admins: [1]
      }
      |> Repo.insert()

    user =
      %Tornium.Schema.User{
        tid: 1,
        name: "Chedburn",
        level: 15
      }
      |> Repo.insert()

    key =
      %Tornium.Schema.TornKey{
        api_key: "asdf1234asdf1234",
        user_id: 1,
        default: true,
        paused: false,
        disabled: false,
        access_level: 3
      }
      |> Repo.insert()

    admin_keys = Tornium.Guild.get_admin_keys(1)
    assert Kernel.length(admin_keys) == 1
    assert Enum.at(admin_keys, 0) == "asdf1234asdf1234"
  end

  test "test_get_admin_keys_multiple" do
    server =
      %Tornium.Schema.Server{
        sid: 2,
        name: "Test server 2",
        admins: [2]
      }
      |> Repo.insert()

    user =
      %Tornium.Schema.User{
        tid: 2,
        name: "Quack",
        level: 15
      }
      |> Repo.insert()

    key_1 =
      %Tornium.Schema.TornKey{
        api_key: "asdfqwerty123456",
        user_id: 2,
        default: false,
        paused: false,
        disabled: false,
        access_level: 3
      }
      |> Repo.insert()

    key_2 =
      %Tornium.Schema.TornKey{
        api_key: "1234567890123456",
        user_id: 2,
        default: true,
        paused: false,
        disabled: false,
        access_level: 3
      }
      |> Repo.insert()

    admin_keys = Tornium.Guild.get_admin_keys(2)
    assert Kernel.length(admin_keys) == 1
    assert Enum.at(admin_keys, 0) == "1234567890123456"
  end

  test "test_get_admin_keys_multiple_users" do
    server =
      %Tornium.Schema.Server{
        sid: 3,
        name: "Test server 3",
        admins: [3, 4]
      }
      |> Repo.insert()

    user_1 =
      %Tornium.Schema.User{
        tid: 3,
        name: "Quack",
        level: 15
      }
      |> Repo.insert()

    user_2 =
      %Tornium.Schema.User{
        tid: 4,
        name: "Quacks",
        level: 15
      }
      |> Repo.insert()

    key_1 =
      %Tornium.Schema.TornKey{
        api_key: "asdfqwerty123456",
        user_id: 3,
        default: true,
        paused: false,
        disabled: false,
        access_level: 3
      }
      |> Repo.insert()

    key_2 =
      %Tornium.Schema.TornKey{
        api_key: "1234567890123456",
        user_id: 4,
        default: true,
        paused: false,
        disabled: false,
        access_level: 3
      }
      |> Repo.insert()

    admin_keys = Tornium.Guild.get_admin_keys(3)
    assert Kernel.length(admin_keys) == 2
    assert Enum.at(admin_keys, 0) == "asdfqwerty123456"
    assert Enum.at(admin_keys, 1) == "1234567890123456"
  end
end
