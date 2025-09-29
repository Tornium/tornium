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

defmodule Tornium.Test.Guild.Verify.Logic do
  use Tornium.RepoCase

  test "test_empty_tempate_verified_name" do
    state =
      Tornium.Guild.Verify.Logic.set_verified_name(
        %{},
        %Tornium.Guild.Verify.Config{
          verify_enabled: true,
          auto_verify_enabled: true,
          gateway_verify_enabled: true,
          verify_template: "",
          verified_roles: [2, 3],
          exclusion_roles: [1],
          faction_verify: %{},
          verify_log_channel: nil,
          verify_jail_channel: nil
        },
        %Tornium.Schema.User{
          tid: 1,
          name: "Chedburn"
        }
      )

    assert is_nil(Map.get(state, :nick))
  end

  test "test_valid_template_verified_name" do
    state =
      Tornium.Guild.Verify.Logic.set_verified_name(
        %{},
        %Tornium.Guild.Verify.Config{
          verify_enabled: true,
          auto_verify_enabled: true,
          gateway_verify_enabled: true,
          verify_template: "{{ name }} [{{ tid }}]",
          verified_roles: [2, 3],
          exclusion_roles: [1],
          faction_verify: %{},
          verify_log_channel: nil,
          verify_jail_channel: nil
        },
        %Tornium.Schema.User{
          tid: 1,
          name: "Chedburn",
          faction: %Tornium.Schema.Faction{
            tid: 1,
            name: "Chedburn Test Faction",
            tag: "Ched"
          }
        }
      )

    assert Map.get(state, :nick) == "Chedburn [1]"
  end

  test "test_verified_roles" do
    state =
      Tornium.Guild.Verify.Logic.set_verified_roles(
        %{},
        %Tornium.Guild.Verify.Config{
          verify_enabled: true,
          auto_verify_enabled: true,
          gateway_verify_enabled: true,
          verify_template: "{{ name }} [{{ tid }}]",
          verified_roles: [2, 3],
          exclusion_roles: [1],
          faction_verify: %{},
          verify_log_channel: nil,
          verify_jail_channel: nil
        },
        %Tornium.Schema.User{
          tid: 1,
          name: "Chedburn"
        }
      )

    assert MapSet.to_list(Map.get(state, :roles)) == [2, 3]
  end

  test "test_empty_verified_roles" do
    state =
      Tornium.Guild.Verify.Logic.set_verified_roles(
        %{},
        %Tornium.Guild.Verify.Config{
          verify_enabled: true,
          auto_verify_enabled: true,
          gateway_verify_enabled: true,
          verify_template: "{{ name }} [{{ tid }}]",
          verified_roles: [],
          exclusion_roles: [1],
          faction_verify: %{},
          verify_log_channel: nil,
          verify_jail_channel: nil
        },
        %Tornium.Schema.User{
          tid: 1,
          name: "Chedburn"
        }
      )

    assert MapSet.to_list(Map.get(state, :roles)) == []
  end

  test "test_remove_invalid_roles" do
    state =
      Tornium.Guild.Verify.Logic.remove_invalid_faction_roles(
        %{roles: MapSet.new([1, 2, 3])},
        %Tornium.Guild.Verify.Config{
          verify_enabled: true,
          auto_verify_enabled: true,
          gateway_verify_enabled: true,
          verify_template: "{{ name }} [{{ tid }}]",
          verified_roles: [],
          exclusion_roles: [1],
          faction_verify: %{
            "1" => %{"roles" => [1], "positions" => %{}, "enabled" => true},
            "2" => %{"roles" => [2], "positions" => %{}, "enabled" => false},
            "3" => %{"roles" => [3], "positions" => %{}, "enabled" => true}
          },
          verify_log_channel: nil,
          verify_jail_channel: nil
        },
        %Tornium.Schema.User{
          tid: 1,
          name: "Chedburn",
          faction: %Tornium.Schema.Faction{
            tid: 1,
            name: "Chedburn Test Faction"
          }
        }
      )

    assert MapSet.to_list(Map.get(state, :roles)) == [1, 2]
  end

  test "test_faction_roles" do
    state =
      Tornium.Guild.Verify.Logic.set_faction_roles(
        %{roles: MapSet.new([2])},
        %Tornium.Guild.Verify.Config{
          verify_enabled: true,
          auto_verify_enabled: true,
          gateway_verify_enabled: true,
          verify_template: "{{ name }} [{{ tid }}]",
          verified_roles: [],
          exclusion_roles: [1],
          faction_verify: %{
            "1" => %{"roles" => [1], "positions" => %{}, "enabled" => true},
            "2" => %{"roles" => [2], "positions" => %{}, "enabled" => false},
            "3" => %{"roles" => [3], "positions" => %{}, "enabled" => true}
          },
          verify_log_channel: nil,
          verify_jail_channel: nil
        },
        %Tornium.Schema.User{
          tid: 1,
          name: "Chedburn",
          faction: %Tornium.Schema.Faction{
            tid: 1,
            name: "Chedburn Test Faction"
          }
        }
      )

    assert MapSet.to_list(Map.get(state, :roles)) == [1, 2]
  end

  test "test_faction_position_roles" do
    state =
      Tornium.Guild.Verify.Logic.set_faction_position_roles(
        %{roles: MapSet.new([2])},
        %Tornium.Guild.Verify.Config{
          verify_enabled: true,
          auto_verify_enabled: true,
          gateway_verify_enabled: true,
          verify_template: "{{ name }} [{{ tid }}]",
          verified_roles: [],
          exclusion_roles: [1],
          faction_verify: %{
            "1" => %{"roles" => [1], "positions" => %{"cbaf7f5d-34c0-4e92-bc4b-cea429bbd496" => [1]}, "enabled" => true},
            "2" => %{"roles" => [2], "positions" => %{}, "enabled" => false},
            "3" => %{"roles" => [3], "positions" => %{}, "enabled" => true}
          },
          verify_log_channel: nil,
          verify_jail_channel: nil
        },
        %Tornium.Schema.User{
          tid: 1,
          name: "Chedburn",
          faction: %Tornium.Schema.Faction{
            tid: 1,
            name: "Chedburn Test Faction"
          },
          faction_position_id: "cbaf7f5d-34c0-4e92-bc4b-cea429bbd496",
          faction_position: %Tornium.Schema.FactionPosition{
            pid: "cbaf7f5d-34c0-4e92-bc4b-cea429bbd496",
            name: "Test Position 1",
            faction_tid: 1
          }
        }
      )

    assert MapSet.to_list(Map.get(state, :roles)) == [1, 2]
  end

  test "test_remove_faction_position_roles" do
    state =
      Tornium.Guild.Verify.Logic.remove_invalid_faction_position_roles(
        %{roles: MapSet.new([1, 2])},
        %Tornium.Guild.Verify.Config{
          verify_enabled: true,
          auto_verify_enabled: true,
          gateway_verify_enabled: true,
          verify_template: "{{ name }} [{{ tid }}]",
          verified_roles: [],
          exclusion_roles: [1],
          faction_verify: %{
            "1" => %{"roles" => [1], "positions" => %{"cbaf7f5d-34c0-4e92-bc4b-cea429bbd497" => [1]}, "enabled" => true},
            "2" => %{"roles" => [2], "positions" => %{}, "enabled" => false},
            "3" => %{"roles" => [3], "positions" => %{}, "enabled" => true}
          },
          verify_log_channel: nil,
          verify_jail_channel: nil
        },
        %Tornium.Schema.User{
          tid: 1,
          name: "Chedburn",
          faction: %Tornium.Schema.Faction{
            tid: 1,
            name: "Chedburn Test Faction"
          },
          faction_position: %Tornium.Schema.FactionPosition{
            pid: "cbaf7f5d-34c0-4e92-bc4b-cea429bbd496",
            name: "Test Position 1",
            faction_tid: 1
          }
        }
      )

    assert MapSet.to_list(Map.get(state, :roles)) == [2]
  end

  test "test_unverified_roles" do
    state = %{roles: MapSet.new([1, 2, 3])}

    config = %Tornium.Guild.Verify.Config{
      verify_enabled: true,
      auto_verify_enabled: true,
      gateway_verify_enabled: true,
      verify_template: "{{ name }} [{{ tid }}]",
      verified_roles: [1],
      unverified_roles: [4],
      exclusion_roles: [],
      faction_verify: %{},
      verify_log_channel: nil,
      verify_jail_channel: nil
    }

    updated_state =
      state
      |> Tornium.Guild.Verify.Logic.remove_invalid_verified_roles(config, nil)
      |> Tornium.Guild.Verify.Logic.set_unverified_roles(config, nil)

    assert MapSet.to_list(Map.get(updated_state, :roles)) == [2, 3, 4]
  end
end
