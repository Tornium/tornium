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

defmodule Tornium.Test.Guild.Verify do
  use Tornium.RepoCase

  test "test_empty_tempate_verified_name" do
    state =
      Tornium.Guild.Verify.set_verified_name(
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

    assert Map.get(state, "nick") == nil
  end

  test "test_valid_template_verified_name" do
    state =
      Tornium.Guild.Verify.set_verified_name(
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

    assert Map.get(state, "nick") == "Chedburn [1]"
  end

  test "test_verified_roles" do
    state =
      Tornium.Guild.Verify.set_verified_roles(
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
      Tornium.Guild.Verify.set_verified_roles(
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
end
