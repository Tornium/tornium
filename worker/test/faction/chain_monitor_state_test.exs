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

defmodule Tornium.Test.Faction.ChainMonitor.State do
  use Tornium.RepoCase, async: true
  alias Tornium.Faction.ChainMonitor
  alias Tornium.Faction.ChainMonitor.State

  @api_key Application.compile_env(:tornium, :api_key)
  @server_id System.unique_integer([:positive])
  @faction_id System.unique_integer([:positive])
  @user_id System.unique_integer([:positive])

  setup_all do
    %Tornium.Schema.Server{sid: @server_id, name: "Test server", factions: [@faction_id]} |> Repo.insert!()
    %Tornium.Schema.Faction{tid: @faction_id, name: "#{@faction_id}", guild_id: @server_id} |> Repo.insert!()

    %Tornium.Schema.ServerAttackConfig{server_id: @server_id, faction_id: @faction_id, chain_alert_channel: 1}
    |> Repo.insert!()

    if not is_nil(@api_key) do
      %Tornium.Schema.User{tid: @user_id, name: "#{@user_id}", faction_id: @faction_id, faction_aa: true}
      |> Repo.insert()

      %Tornium.Schema.TornKey{
        user_id: @user_id,
        api_key: "api_key_#{@user_id}",
        default: true,
        disabled: false,
        paused: false,
        access_level: :full
      }
      |> Repo.insert()
    end

    %{}
  end

  defp ago(s) do
    DateTime.add(DateTime.utc_now(), -s, :second)
  end

  defp state(attrs) do
    struct!(
      State,
      Keyword.merge(
        [
          faction_id: @faction_id,
          chain_id: 1,
          chain_length: 0,
          last_updated: DateTime.utc_now(),
          last_attack: nil,
          timer_ref: nil
        ],
        attrs
      )
    )
  end

  test "waits while chain is at 0" do
    assert {:noreply, %State{}} = ChainMonitor.handle_continue(:message, state(chain_length: 0))
  end

  test "stops when chain is in cooldown" do
    assert {:stop, {:shutdown, _}, _} =
             ChainMonitor.handle_continue(:message, state(chain_length: 50, last_attack: nil))
  end

  test "alerts when time left is under the minimum" do
    assert {:noreply, _} = ChainMonitor.handle_continue(:message, state(chain_length: 150, last_attack: ago(270)))

    assert_received {:chain_monitor_message, @faction_id, %{content: "Chain Alert!!!"}}
  end

  test "no alert when time left is above the minimum" do
    assert {:noreply, _} = ChainMonitor.handle_continue(:message, state(chain_length: 150, last_attack: ago(30)))

    refute_received {:chain_monitor_message, @faction_id, %{content: "Chain Alert!!!"}}
  end

  test "stops and notifies when the timer has expired" do
    assert {:stop, {:shutdown, _}, _} =
             ChainMonitor.handle_continue(:message, state(chain_length: 150, last_attack: ago(310)))

    assert_received {:chain_monitor_message, @faction_id, %{content: "ChainMonitor has stopped" <> _}}
  end

  test "stops when the alert channel was removed mid-chain" do
    ChainMonitor.disable(0)

    assert {:stop, {:shutdown, _}, _} =
             ChainMonitor.handle_continue(:message, state(chain_length: 150, last_attack: ago(30)))
  end

  test "stops a stale chain under 100 hits" do
    assert {:stop, {:shutdown, _}, _} =
             ChainMonitor.handle_continue(:message, state(chain_length: 50, last_attack: ago(400)))
  end
end
