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

defmodule Tornium.Test.User.KeyStore do
  use Tornium.RepoCase

  test "test_invalid_key" do
    pid = ExUnit.Callbacks.start_link_supervised!(Tornium.User.KeyStore)

    api_key = %Tornium.Schema.TornKey{
      guid: nil,
      api_key: "asdf1234asdf1234",
      user_id: 1,
      default: true,
      paused: false,
      disabled: false,
      access_level: 3
    }

    assert Tornium.User.KeyStore.put(pid, 1, api_key) == :ok
    assert is_nil(Tornium.User.KeyStore.get(pid, 2))

    Agent.stop(pid)
  end

  test "test_valid_key" do
    {:ok, pid} = ExUnit.Callbacks.start_supervised(Tornium.User.KeyStore)

    api_key = %Tornium.Schema.TornKey{
      guid: nil,
      api_key: "asdf1234asdf1234",
      user_id: 1,
      default: true,
      paused: false,
      disabled: false,
      access_level: 3
    }

    assert Tornium.User.KeyStore.put(pid, 1, api_key) == :ok
    assert Tornium.User.KeyStore.get(pid, 1) == api_key

    Agent.stop(pid)
  end

  test "test_key_expiration" do
    {:ok, pid} = ExUnit.Callbacks.start_supervised(Tornium.User.KeyStore)

    api_key = %Tornium.Schema.TornKey{
      guid: nil,
      api_key: "asdf1234asdf1234",
      user_id: 1,
      default: true,
      paused: false,
      disabled: false,
      access_level: 3
    }

    assert Tornium.User.KeyStore.put(pid, 1, api_key, 1) == :ok
    assert Tornium.User.KeyStore.get(pid, 1) == api_key

    Process.sleep(1000)
    assert is_nil(Tornium.User.KeyStore.get(pid, 1))

    Agent.stop(pid)
  end
end
