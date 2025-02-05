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

defmodule Tornium.Test.User.Update do
  use Tornium.RepoCase

  test "test_user_update_api_error" do
    assert Tornium.User.update_user_data(%{"error" => %{"code" => 6, "error" => "Incorrect ID"}}, nil) ==
             {:error, %Tornium.API.Error{code: 6, error: "Incorrect ID", message: "Wrong ID value."}}
  end

  test "test_user_update" do
    update_return =
      Tornium.User.update_user_data(
        %{
          "player_id" => 1,
          "name" => "Chedburn",
          "level" => 15,
          "last_action" => %{"status" => "Offline", "timestamp" => 1_704_088_800},
          "discord" => %{"discordID" => 317_719_897_578_799_114},
          "faction" => %{
            "faction_id" => 42113,
            "faction_name" => "TEs_t!.@&#039;",
            "faction_tag" => "ÃÃ©â„",
            "position" => "Leader"
          }
        },
        :tid
      )

    assert not is_nil(update_return)
    assert update_return == {:ok, true}

    db_user =
      Tornium.Schema.User
      |> where([u], u.tid == 1)
      |> Repo.one()

    assert db_user.level == 15
    assert db_user.name == "Chedburn"

    db_faction =
      Tornium.Schema.Faction
      |> where([f], f.tid == 42113)
      |> Repo.one()

    assert db_faction.name == "TEs_t!.@&#039;"
  end

  test "test_user_update_self" do
    update_return =
      Tornium.User.update_user_data(
        %{
          "player_id" => 2,
          "name" => "Quack",
          "level" => 15,
          "strength" => 10,
          "defense" => 10,
          "speed" => 10,
          "dexterity" => 10,
          "last_action" => %{"status" => "Offline", "timestamp" => 1_704_088_800},
          "discord" => %{"discordID" => nil},
          "faction" => %{
            "faction_id" => 42113,
            "faction_name" => "TEs_t!.@&#039;",
            "faction_tag" => "ÃÃ©â„",
            "position" => "Co-leader"
          }
        },
        :self
      )

    assert not is_nil(update_return)
    assert update_return == {:ok, true}

    db_user =
      Tornium.Schema.User
      |> where([u], u.tid == 2)
      |> Repo.one()

    assert db_user.strength == 10
    assert db_user.battlescore == 4 * :math.sqrt(10)
  end
end
