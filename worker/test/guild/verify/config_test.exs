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
    Tornium.Schema.Server.new(1, "Test server",
      admins: [1],
      verify_enabled: true,
      auto_verify_enabled: true,
      gateway_verify_enabled: true,
      verify_template: "{{ name }} [{{ tid }}]",
      verified_roles: [123],
      exclusion_roles: [],
      faction_verify: %{},
      verify_log_channel: 0,
      verify_jail_channel: 0
    )

    assert %Tornium.Guild.Verify.Config{
             verify_enabled: true,
             auto_verify_enabled: true,
             gateway_verify_enabled: true,
             verify_template: "{{ name }} [{{ tid }}]",
             verified_roles: [123],
             exclusion_roles: [],
             faction_verify: %{},
             verify_log_channel: 0,
             verify_jail_channel: 0
           } = Tornium.Guild.Verify.Config.validate(1)
  end
end
