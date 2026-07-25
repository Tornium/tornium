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

defmodule Tornium.Test.Faction.ChainMonitor do
  use Tornium.RepoCase, async: false
  alias Tornium.Faction.ChainMonitor

  @api_key Application.compile_env(:tornium, :api_key)

  defp setup do
    %Tornium.Schema.Server{sid: 1, name: "Test server", factions: [0, 1]} |> Repo.insert!()
    %Tornium.Schema.Faction{tid: 0, name: "0", guild_id: 1} |> Repo.insert!()
    %Tornium.Schema.Faction{tid: 1, name: "1", guild_id: 1} |> Repo.insert!()
    %Tornium.Schema.ServerAttackConfig{server_id: 1, faction_id: 0, chain_alert_channel: 1} |> Repo.insert!()
    %Tornium.Schema.ServerAttackConfig{server_id: 1, faction_id: 1, chain_alert_channel: nil} |> Repo.insert!()

    if not is_nil(@api_key) do
      %Tornium.Schema.User{tid: 1, name: "Chedburn", faction_id: 0, faction_aa: true} |> Repo.insert()

      %Tornium.Schema.TornKey{
        user_id: 1,
        api_key: @api_key,
        default: true,
        disabled: false,
        paused: false,
        access_level: :full
      }
      |> Repo.insert()
    end
  end

  @tag :integration
  test "check configuration" do
    setup()

    {:error, _} = ChainMonitor.start_link(faction_id: 2)
    {:error, _} = ChainMonitor.start_link(faction_id: 1)
    {:ok, pid} = ChainMonitor.start_link(faction_id: 0)

    assert is_pid(pid)
    GenServer.stop(pid)
  end

  test "stops the genserver if chain timer has ended (<= 0 seconds left)" do
    setup()
    {:ok, pid} = ChainMonitor.start_link(faction_id: 0)

    last_attack = DateTime.add(DateTime.utc_now(), -301, :second)

    state = %Tornium.Faction.ChainMonitor.State{
      faction_id: 0,
      last_attack: last_attack,
      chain_length: 1500
    }

    assert {:stop, "Stopped ChainMonitor as chain has ended for faction 0"} =
             ChainMonitor.handle_continue(:message, state)

    GenServer.stop(pid)
  end

  test "re-queues the timer when chain length is below 100 hits" do
    setup()
    {:ok, pid} = ChainMonitor.start_link(faction_id: 0)

    state = %Tornium.Faction.ChainMonitor.State{
      faction_id: 0,
      chain_length: 50,
      last_updated: DateTime.utc_now(),
      last_attack: DateTime.utc_now()
    }

    assert {:noreply, new_state} = ChainMonitor.handle_continue(:message, state)
    assert not is_nil(new_state.timer_ref)

    ChainMonitor.State.cancel_existing_timer(new_state)
    GenServer.stop(pid)
  end
end
