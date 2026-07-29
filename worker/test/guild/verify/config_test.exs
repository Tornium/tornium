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

defmodule Tornium.Test.Guild.Verify.Config do
  use Tornium.RepoCase

  test "test_config_validation" do
    assert Tornium.Guild.Verify.Config.validate(%Tornium.Schema.Server{
             sid: 1,
             name: "Test server",
             admins: [1],
             verify_enabled: true,
             auto_verify_enabled: true,
             gateway_verify_enabled: true,
             verify_template: "{{ name }} [{{ tid }}]",
             verified_roles: [123],
             exclusion_roles: [456],
             faction_verify: %{},
             verify_log_channel: 1,
             verify_jail_channel: 2
           }) == %Tornium.Guild.Verify.Config{
             verify_enabled: true,
             auto_verify_enabled: true,
             gateway_verify_enabled: true,
             verify_template: "{{ name }} [{{ tid }}]",
             verified_roles: [123],
             exclusion_roles: [456],
             faction_verify: %{},
             verify_log_channel: 1,
             verify_jail_channel: 2
           }
  end

  test "config validatation with string position roles" do
    position_id = Ecto.UUID.generate()

    parsed_config =
      Tornium.Guild.Verify.Config.validate(%Tornium.Schema.Server{
        sid: 1,
        name: "Test server",
        admins: [1],
        verify_enabled: true,
        auto_verify_enabled: true,
        gateway_verify_enabled: true,
        verify_template: "{{ name }} [{{ tid }}]",
        verified_roles: [],
        exclusion_roles: [],
        faction_verify: %{"1" => %{"roles" => [1], "enabled" => true, "positions" => %{position_id => [123, "456"]}}},
        verify_log_channel: 0,
        verify_jail_channel: 0
      })

    assert %Tornium.Guild.Verify.Config{
             verify_enabled: true,
             auto_verify_enabled: true,
             gateway_verify_enabled: true,
             verify_template: "{{ name }} [{{ tid }}]",
             verified_roles: [],
             exclusion_roles: [],
             faction_verify: %{
               "1" => %{"roles" => [1], "enabled" => true, "positions" => %{^position_id => [123, 456]}}
             },
             verify_log_channel: 0,
             verify_jail_channel: 0
           } = parsed_config
  end
end
