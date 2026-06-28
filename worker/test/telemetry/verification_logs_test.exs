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

defmodule Tornium.Test.Telemetry.VerificationLogs do
  use Tornium.RepoCase, async: true

  setup do
    table = :ets.new(:verification_logs_test, [:duplicate_bag, :public])

    on_exit(fn ->
      if :ets.info(table) != :undefined do
        :ets.delete(table)
      end
    end)

    {:ok, table: table}
  end

  test "insert invalid", %{table: table} do
    assert_raise FunctionClauseError, fn ->
      Tornium.Telemetry.VerificationLogs.insert(
        nil,
        %Tornium.Schema.VerificationLog{},
        %Nostrum.Struct.Message{},
        table: table
      )
    end

    assert_raise FunctionClauseError, fn -> Tornium.Telemetry.VerificationLogs.insert(1, nil, nil, table: table) end
  end

  test "insert valid with different keys", %{table: table} do
    Tornium.Telemetry.VerificationLogs.insert(1, nil, %Nostrum.Struct.Message{content: "test"}, table: table)
    Tornium.Telemetry.VerificationLogs.insert(2, %Tornium.Schema.VerificationLog{}, nil, table: table)

    # TODO: Validate ETS values
  end

  test "insert valid duplicate keys", %{table: table} do
    Tornium.Telemetry.VerificationLogs.insert(1, nil, %Nostrum.Struct.Message{content: "test"}, table: table)
    Tornium.Telemetry.VerificationLogs.insert(1, nil, %Nostrum.Struct.Message{content: "test 2"}, table: table)

    # TODO: Validate ETS values
  end

  test "get guilds", %{table: table} do
    Tornium.Telemetry.VerificationLogs.insert(1, nil, %Nostrum.Struct.Message{content: "test"}, table: table)
    Tornium.Telemetry.VerificationLogs.insert(1, nil, %Nostrum.Struct.Message{content: "test 2"}, table: table)
    Tornium.Telemetry.VerificationLogs.insert(2, %Tornium.Schema.VerificationLog{}, nil, table: table)

    guilds = Tornium.Telemetry.VerificationLogs.take_guilds(table)
    assert guilds == MapSet.new([1, 2])
  end

  test "get all", %{table: table} do
    Tornium.Telemetry.VerificationLogs.insert(1, nil, %Nostrum.Struct.Message{content: "test"}, table: table)
    Tornium.Telemetry.VerificationLogs.insert(2, %Tornium.Schema.VerificationLog{}, nil, table: table)

    assert %{1 => one, 2 => two} = Tornium.Telemetry.VerificationLogs.take(table)
    assert [{nil, nil, nil, %Nostrum.Struct.Message{content: "test"}}] = one
    assert [{nil, nil, %Tornium.Schema.VerificationLog{}, nil}] = two
  end
end
