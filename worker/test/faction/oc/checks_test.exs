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

defmodule Tornium.Test.Faction.OC.Checks do
  use Tornium.RepoCase

  test "test_oc_no_tool" do
    crime = %Tornium.Schema.OrganizedCrime{
      oc_id: 1,
      oc_name: "Test",
      oc_difficulty: 1,
      faction_id: 1,
      faction: %Tornium.Schema.Faction{},
      status: :planning,
      created_at: DateTime.utc_now(),
      planning_started_at: nil,
      ready_at: nil,
      expires_at: DateTime.utc_now(),
      executed_at: nil,
      slots: [
        %Tornium.Schema.OrganizedCrimeSlot{
          id: Ecto.UUID.generate(),
          oc_id: 1,
          oc: nil,
          slot_index: 0,
          crime_position: "Muscle",
          user_id: 1,
          user: %Tornium.Schema.User{
            tid: 1,
            name: "Chedburn"
          },
          user_success_chance: 99,
          item_required_id: nil,
          item_required: nil,
          item_available: false,
          delayer: false,
          delayed_reason: nil,
          sent_tool_notification: false
        }
      ]
    }

    %Tornium.Faction.OC.Check.Struct{missing_tools: missing_tools} =
      Tornium.Faction.OC.Check.Struct.new() |> Tornium.Faction.OC.Check.check_tools(crime)

    assert Kernel.length(missing_tools) == 0
  end

  test "test_oc_missing_tool" do
    crime = %Tornium.Schema.OrganizedCrime{
      oc_id: 1,
      oc_name: "Test",
      oc_difficulty: 1,
      faction_id: 1,
      faction: %Tornium.Schema.Faction{},
      status: :planning,
      created_at: DateTime.utc_now(),
      planning_started_at: nil,
      ready_at: DateTime.add(DateTime.utc_now(), 10, :hour),
      expires_at: DateTime.utc_now(),
      executed_at: nil,
      slots: [
        %Tornium.Schema.OrganizedCrimeSlot{
          id: Ecto.UUID.generate(),
          oc_id: 1,
          oc: nil,
          slot_index: 0,
          crime_position: "Muscle",
          user_id: 1,
          user: %Tornium.Schema.User{
            tid: 1,
            name: "Chedburn"
          },
          user_success_chance: 99,
          item_required_id: 206,
          item_required: %Tornium.Schema.Item{
            tid: 206,
            name: "Xanax"
          },
          item_available: false,
          delayer: false,
          delayed_reason: nil,
          sent_tool_notification: false
        }
      ]
    }

    %Tornium.Faction.OC.Check.Struct{missing_tools: missing_tools} =
      Tornium.Faction.OC.Check.Struct.new() |> Tornium.Faction.OC.Check.check_tools(crime)

    assert Kernel.length(missing_tools) == 1
    assert Enum.at(missing_tools, 0).user_id == 1
    assert Enum.at(missing_tools, 0).item_required_id == 206
  end

  test "test_oc_missing_tool_too_new" do
    crime = %Tornium.Schema.OrganizedCrime{
      oc_id: 1,
      oc_name: "Test",
      oc_difficulty: 1,
      faction_id: 1,
      faction: %Tornium.Schema.Faction{},
      status: :planning,
      created_at: DateTime.utc_now(),
      planning_started_at: nil,
      ready_at: DateTime.add(DateTime.utc_now(), 72, :hour),
      expires_at: DateTime.utc_now(),
      executed_at: nil,
      slots: [
        %Tornium.Schema.OrganizedCrimeSlot{
          id: Ecto.UUID.generate(),
          oc_id: 1,
          oc: nil,
          slot_index: 0,
          crime_position: "Muscle",
          user_id: 1,
          user: %Tornium.Schema.User{
            tid: 1,
            name: "Chedburn"
          },
          user_success_chance: 99,
          item_required_id: 206,
          item_required: %Tornium.Schema.Item{
            tid: 206,
            name: "Xanax"
          },
          item_available: false,
          delayer: false,
          delayed_reason: nil,
          sent_tool_notification: false
        }
      ]
    }

    %Tornium.Faction.OC.Check.Struct{missing_tools: missing_tools} =
      Tornium.Faction.OC.Check.Struct.new() |> Tornium.Faction.OC.Check.check_tools(crime)

    assert Kernel.length(missing_tools) == 0
  end

  test "test_oc_has_tool" do
    crime = %Tornium.Schema.OrganizedCrime{
      oc_id: 1,
      oc_name: "Test",
      oc_difficulty: 1,
      faction_id: 1,
      faction: %Tornium.Schema.Faction{},
      status: :planning,
      created_at: DateTime.utc_now(),
      planning_started_at: nil,
      ready_at: nil,
      expires_at: DateTime.utc_now(),
      executed_at: nil,
      slots: [
        %Tornium.Schema.OrganizedCrimeSlot{
          id: Ecto.UUID.generate(),
          oc_id: 1,
          oc: nil,
          slot_index: 0,
          crime_position: "Muscle",
          user_id: 1,
          user: %Tornium.Schema.User{
            tid: 1,
            name: "Chedburn"
          },
          user_success_chance: 99,
          item_required_id: 206,
          item_required: %Tornium.Schema.Item{
            tid: 206,
            name: "Xanax"
          },
          item_available: true,
          delayer: false,
          delayed_reason: nil,
          sent_tool_notification: false
        }
      ]
    }

    %Tornium.Faction.OC.Check.Struct{missing_tools: missing_tools} =
      Tornium.Faction.OC.Check.Struct.new() |> Tornium.Faction.OC.Check.check_tools(crime)

    assert Kernel.length(missing_tools) == 0
  end

  test "test_not_ready_oc" do
    crime = %Tornium.Schema.OrganizedCrime{
      oc_id: 1,
      oc_name: "Test",
      oc_difficulty: 1,
      faction_id: 1,
      faction: %Tornium.Schema.Faction{},
      status: :planning,
      created_at: DateTime.utc_now(),
      planning_started_at: nil,
      ready_at: nil,
      expires_at: DateTime.utc_now(),
      executed_at: nil,
      slots: [
        %Tornium.Schema.OrganizedCrimeSlot{
          id: Ecto.UUID.generate(),
          oc_id: 1,
          oc: nil,
          slot_index: 0,
          crime_position: "Muscle",
          user_id: 1,
          user: %Tornium.Schema.User{
            tid: 1,
            name: "Chedburn"
          },
          user_success_chance: 99,
          item_required_id: nil,
          item_required: nil,
          item_available: true,
          delayer: false,
          delayed_reason: nil,
          sent_tool_notification: false
        }
      ]
    }

    %Tornium.Faction.OC.Check.Struct{delayers: delayers} =
      Tornium.Faction.OC.Check.Struct.new() |> Tornium.Faction.OC.Check.check_delayers(crime)

    assert Kernel.length(delayers) == 0
  end

  test "test_ready_delayed_oc" do
    crime = %Tornium.Schema.OrganizedCrime{
      oc_id: 1,
      oc_name: "Test",
      oc_difficulty: 1,
      faction_id: 1,
      faction: %Tornium.Schema.Faction{},
      status: :planning,
      created_at: DateTime.utc_now(),
      planning_started_at: nil,
      ready_at: DateTime.add(DateTime.utc_now(), -10, :minute),
      expires_at: DateTime.utc_now(),
      executed_at: nil,
      slots: [
        %Tornium.Schema.OrganizedCrimeSlot{
          id: Ecto.UUID.generate(),
          oc_id: 1,
          oc: nil,
          slot_index: 0,
          crime_position: "Muscle",
          user_id: 1,
          user: %Tornium.Schema.User{
            tid: 1,
            name: "Chedburn"
          },
          user_success_chance: 99,
          item_required_id: nil,
          item_required: nil,
          item_available: true,
          delayer: true,
          delayed_reason: "Not writing new crimes",
          sent_tool_notification: false
        }
      ]
    }

    %Tornium.Faction.OC.Check.Struct{delayers: delayers} =
      Tornium.Faction.OC.Check.Struct.new() |> Tornium.Faction.OC.Check.check_delayers(crime)

    assert Kernel.length(delayers) == 1
    assert Enum.at(delayers, 0).user_id == 1
    assert Enum.at(delayers, 0).delayer == true
  end

  test "test_ready_not_delayed_oc" do
    crime = %Tornium.Schema.OrganizedCrime{
      oc_id: 1,
      oc_name: "Test",
      oc_difficulty: 1,
      faction_id: 1,
      faction: %Tornium.Schema.Faction{},
      status: :planning,
      created_at: DateTime.utc_now(),
      planning_started_at: nil,
      ready_at: DateTime.add(DateTime.utc_now(), -10, :minute),
      expires_at: DateTime.utc_now(),
      executed_at: nil,
      slots: [
        %Tornium.Schema.OrganizedCrimeSlot{
          id: Ecto.UUID.generate(),
          oc_id: 1,
          oc: nil,
          slot_index: 0,
          crime_position: "Muscle",
          user_id: 1,
          user: %Tornium.Schema.User{
            tid: 1,
            name: "Chedburn"
          },
          user_success_chance: 99,
          item_required_id: nil,
          item_required: nil,
          item_available: true,
          delayer: false,
          delayed_reason: nil,
          sent_tool_notification: false
        }
      ]
    }

    %Tornium.Faction.OC.Check.Struct{delayers: delayers} =
      Tornium.Faction.OC.Check.Struct.new() |> Tornium.Faction.OC.Check.check_delayers(crime)

    assert Kernel.length(delayers) == 0
  end
end
