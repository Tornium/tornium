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

  test "test_user_update" do
    update_return =
      Tornium.User.update_data(
        Tornex.SpecQuery.parse(
          %Tornex.SpecQuery{
            paths: [Torngen.Client.Path.User.Id.Profile, Torngen.Client.Path.User.Id.Discord],
            parameters: [id: 1]
          },
          %{
            "profile" => %{
              "id" => 1,
              "name" => "Chedburn",
              "level" => 15,
              "last_action" => %{"status" => "Offline", "timestamp" => 1_704_088_800},
              "faction_id" => 42_113
            },
            "discord" => %{"discord_id" => "317719897578799114", "user_id" => 1}
          }
        )
      )

    assert {:ok, %Tornium.Schema.User{} = user} = update_return

    assert user.level == 15
    assert user.name == "Chedburn"
    assert user.faction_id == 42_113
  end

  test "test_user_update_self" do
    update_return =
      Tornium.User.update_data(
        Tornex.SpecQuery.parse(
          %Tornex.SpecQuery{
            paths: [
              Torngen.Client.Path.User.Profile,
              Torngen.Client.Path.User.Discord,
              Torngen.Client.Path.User.Battlestats
            ]
          },
          %{
            "profile" => %{
              "id" => 2,
              "name" => "Quack",
              "level" => 15,
              "last_action" => %{"status" => "Offline", "timestamp" => 1_704_088_800},
              "faction_id" => 42_113
            },
            "discord" => %{"discord_id" => "", "user_id" => 2},
            "battlestats" => %{
              "strength" => %{"value" => 10, "modifiers" => [], "modifier" => 0},
              "defense" => %{"value" => 10, "modifiers" => [], "modifier" => 0},
              "speed" => %{"value" => 10, "modifiers" => [], "modifier" => 0},
              "dexterity" => %{"value" => 10, "modifiers" => [], "modifier" => 0},
              "total" => 40
            }
          }
        )
      )

    assert {:ok, %Tornium.Schema.User{} = user} = update_return

    assert user.level == 15
    assert user.name == "Quack"
    assert user.faction_id == 42_113

    assert user.strength == 10
    assert user.battlescore == 4 * :math.sqrt(10)
  end

  test "fedded_status" do
    assert is_nil(
             Tornium.User.fedded_until(%{
               "status" => %{
                 "description" => "Okay",
                 "details" => "",
                 "state" => "Okay",
                 "color" => "green",
                 "until" => 0
               }
             })
           )

    assert ~D[2026-03-05] ==
             Tornium.User.fedded_until(%{
               "status" => %{
                 "description" => "In federal jail for 16 days",
                 "details" => "Staff see notes",
                 "state" => "Federal",
                 "color" => "red",
                 "until" => 1_772_668_800
               }
             })

    assert ~D[9999-12-31] ==
             Tornium.User.fedded_until(%{
               "status" => %{
                 "description" => "In federal jail permanently",
                 "details" => "Account marked for deletion",
                 "state" => "Federal",
                 "color" => "red",
                 "until" => 1_857_600_000
               }
             })

    assert ~D[9999-12-31] ==
             Tornium.User.fedded_until(%{
               "status" => %{
                 "description" => "Fallen",
                 "details" => "Resting in Peace",
                 "state" => "Fallen",
                 "color" => "red",
                 "until" => 0
               }
             })
  end
end
