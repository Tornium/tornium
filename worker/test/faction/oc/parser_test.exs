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

defmodule Tornium.Test.Faction.OC.Parser do
  use Tornium.RepoCase

  # TODO: Fill out members
  @members [
    %{
      "id" => 1,
      "name" => "Chedburn",
      "status" => %{"description" => "Okay", "details" => nil, "state" => "Okay", "until" => nil}
    },
    %{
      "id" => 2,
      "name" => "Quack",
      "status" => %{"description" => "Okay", "details" => nil, "state" => "Okay", "until" => nil}
    },
    %{
      "id" => 3,
      "name" => "Duke",
      "status" => %{"description" => "Traveling to Nowhere", "details" => nil, "state" => "Traveling", "until" => nil}
    }
  ]

  test "test_crime_parser" do
    api_data = %{
      "id" => 380_813,
      "name" => "Honey Trap",
      "difficulty" => 6,
      "status" => "Planning",
      "created_at" => 1_741_107_620,
      "initiated_at" => 1_741_111_258,
      "planning_at" => 1_741_111_258,
      "executed_at" => nil,
      "ready_at" => 1_741_370_458,
      "expired_at" => 1_741_366_820,
      "slots" => [],
      "rewards" => nil
    }

    crimes = Tornium.Faction.OC.parse_crimes([api_data], @members, 1, [])

    assert Kernel.length(crimes) == 1

    %Tornium.Schema.OrganizedCrime{
      oc_id: oc_id,
      oc_name: oc_name,
      oc_difficulty: oc_difficulty,
      faction_id: faction_id,
      status: status,
      created_at: created_at,
      planning_started_at: planning_started_at,
      ready_at: ready_at,
      expires_at: expires_at,
      executed_at: executed_at
    } = Enum.at(crimes, 0)

    assert oc_id == 380_813
    assert oc_name == "Honey Trap"
    assert oc_difficulty == 6
    assert status == :planning
    assert DateTime.to_unix(created_at) == 1_741_107_620
    assert DateTime.to_unix(planning_started_at) == 1_741_111_258
    assert DateTime.to_unix(ready_at) == 1_741_370_458
    assert DateTime.to_unix(expires_at) == 1_741_366_820
    assert executed_at == nil
  end

  test "test_slot_parser_not_ready" do
    slots =
      [
        %{
          "position" => "Enforcer",
          "item_requirement" => %{"id" => 1080, "is_reusable" => true, "is_available" => true},
          "user_id" => 1,
          "user" => %{"id" => 1, "joined_at" => 1_741_114_140, "progress" => 44.89},
          "success_chance" => 75
        },
        %{
          "position" => "Muscle",
          "item_requirement" => nil,
          "user_id" => 2,
          "user" => %{"id" => 2, "joined_at" => 1_741_111_258, "progress" => 100},
          "success_chance" => 71
        }
      ]
      |> Tornium.Faction.OC.parse_slots(@members, 380_813, false, [])

    # |> IO.inspect()

    assert Kernel.length(slots) == 2

    %Tornium.Schema.OrganizedCrimeSlot{
      delayer: delayer,
      user_id: user_id,
      oc_id: oc_id,
      crime_position: crime_position,
      user_success_chance: user_success_chance,
      item_required_id: item_required_id,
      item_available: item_available,
      delayed_reason: delayed_reason
    } = Enum.at(slots, 0)

    assert delayer == nil
    assert user_id == 2
    assert oc_id == 380_813
    assert crime_position == "Muscle"
    assert user_success_chance == 71
    assert item_required_id == nil
    assert item_available == nil
    assert delayed_reason == nil

    %Tornium.Schema.OrganizedCrimeSlot{
      delayer: delayer,
      user_id: user_id,
      oc_id: oc_id,
      crime_position: crime_position,
      user_success_chance: user_success_chance,
      item_required_id: item_required_id,
      item_available: item_available,
      delayed_reason: delayed_reason
    } = Enum.at(slots, 1)

    assert delayer == nil
    assert user_id == 1
    assert oc_id == 380_813
    assert crime_position == "Enforcer"
    assert user_success_chance == 75
    assert item_required_id == 1080
    assert item_available == true
    assert delayed_reason == nil
  end

  test "test_slot_parser_ready_delayed" do
    slots =
      [
        %{
          "position" => "Enforcer",
          "item_requirement" => %{"id" => 1080, "is_reusable" => true, "is_available" => true},
          "user_id" => 1,
          "user" => %{"id" => 1, "joined_at" => 1_741_114_140, "progress" => 100},
          "success_chance" => 75
        },
        %{
          "position" => "Muscle",
          "item_requirement" => nil,
          "user_id" => 2,
          "user" => %{"id" => 2, "joined_at" => 1_741_111_258, "progress" => 100},
          "success_chance" => 71
        },
        %{
          "position" => "Muscle",
          "item_requirement" => nil,
          "user_id" => 3,
          "user" => %{"id" => 3, "joined_at" => 1_741_111_258, "progress" => 100},
          "success_chance" => 70
        }
      ]
      |> Tornium.Faction.OC.parse_slots(@members, 380_813, true, [])
      # |> IO.inspect()

    assert Kernel.length(slots) == 3

    %Tornium.Schema.OrganizedCrimeSlot{
      delayer: delayer,
      user_id: user_id,
      oc_id: oc_id,
      crime_position: crime_position,
      user_success_chance: user_success_chance,
      item_required_id: item_required_id,
      item_available: item_available,
      delayed_reason: delayed_reason
    } = Enum.at(slots, 0)

    assert delayer == true
    assert user_id == 3
    assert oc_id == 380_813
    assert crime_position == "Muscle"
    assert user_success_chance == 70
    assert item_required_id == nil
    assert item_available == nil
    assert delayed_reason == "Traveling to Nowhere"

    %Tornium.Schema.OrganizedCrimeSlot{
      delayer: delayer,
      user_id: user_id,
      oc_id: oc_id,
      crime_position: crime_position,
      user_success_chance: user_success_chance,
      item_required_id: item_required_id,
      item_available: item_available,
      delayed_reason: delayed_reason
    } = Enum.at(slots, 1)

    assert delayer == false
    assert user_id == 2
    assert oc_id == 380_813
    assert crime_position == "Muscle"
    assert user_success_chance == 71
    assert item_required_id == nil
    assert item_available == nil
    assert delayed_reason == nil

    %Tornium.Schema.OrganizedCrimeSlot{
      delayer: delayer,
      user_id: user_id,
      oc_id: oc_id,
      crime_position: crime_position,
      user_success_chance: user_success_chance,
      item_required_id: item_required_id,
      item_available: item_available,
      delayed_reason: delayed_reason
    } = Enum.at(slots, 2)

    assert delayer == false
    assert user_id == 1
    assert oc_id == 380_813
    assert crime_position == "Enforcer"
    assert user_success_chance == 75
    assert item_required_id == 1080
    assert item_available == true
    assert delayed_reason == nil
  end
end
