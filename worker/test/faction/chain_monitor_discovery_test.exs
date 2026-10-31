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

defmodule Tornium.Test.Faction.ChainMonitor.Discovery do
  use Tornium.RepoCase, async: false
  alias Tornium.Faction.ChainMonitor.Discovery
  alias Tornium.Repo

  setup do
    start_supervised!(Tornium.Faction.ChainMonitor.Supervisor)

    faction_id = unique_id()
    faction_position_id = Ecto.UUID.generate()
    server_id = unique_id()
    chain_alert_channel = unique_id()
    user_id = unique_id()
    chain_id = unique_id()

    server = Repo.insert!(%Tornium.Schema.Server{sid: server_id, name: "test server", factions: [faction_id]})
    faction = Repo.insert!(%Tornium.Schema.Faction{tid: faction_id, name: "test faction", guild_id: server_id})

    faction_position =
      Repo.insert!(%Tornium.Schema.FactionPosition{
        pid: faction_position_id,
        faction_id: faction_id,
        name: "test position",
        permissions: ["Faction API Access"]
      })

    attack_config =
      Repo.insert!(%Tornium.Schema.ServerAttackConfig{
        server_id: server_id,
        faction_id: faction_id,
        chain_alert_channel: chain_alert_channel
      })

    chain =
      Repo.insert!(%Tornium.Schema.Chain{
        chain_id: chain_id,
        faction_id: faction_id,
        length: 1_234,
        start_timestamp: DateTime.utc_now() |> DateTime.truncate(:second)
      })

    user =
      Repo.insert!(%Tornium.Schema.User{
        tid: user_id,
        name: "test user",
        faction_id: faction_id,
        faction_position_id: faction_position_id,
        faction_aa: true
      })

    api_key =
      Repo.insert!(%Tornium.Schema.TornKey{
        user_id: user_id,
        api_key: "apikey_#{user_id}",
        default: true,
        disabled: false,
        paused: false,
        access_level: :full
      })

    %{
      faction: faction,
      faction_position: faction_position,
      server: server,
      attack_config: attack_config,
      user: user,
      api_key: api_key,
      chain: chain
    }
  end

  defp unique_id() do
    System.unique_integer([:positive])
  end

  defp start_discovery(opts) do
    test_pid = self()
    opts = Keyword.merge([name: :discovery_test, monitor_starter: &send(test_pid, {:started, &1})], opts)

    pid = start_supervised!({Discovery, opts})
    Ecto.Adapters.SQL.Sandbox.allow(Tornium.Repo, self(), pid)

    pid
  end

  describe "chaining_faction_ids/0" do
    test "returns a fully configured faction with an open chain", %{faction: faction, chain: chain} do
      assert Discovery.chaining_faction_ids() == [{faction.tid, chain.chain_id}]
    end

    test "excludes factions whose chain has ended", %{chain: chain} do
      now = DateTime.utc_now() |> DateTime.truncate(:second)

      Tornium.Schema.Chain
      |> where([c], c.chain_id == ^chain.chain_id)
      |> update([c], set: [end_timestamp: ^now])
      |> Repo.update_all([])

      assert Discovery.chaining_faction_ids() == []
    end

    test "excludes factions whose only key is disabled", %{api_key: api_key} do
      Tornium.Schema.TornKey
      |> where([k], k.api_key == ^api_key.api_key)
      |> update([k], set: [disabled: true])
      |> Repo.update_all([])

      assert Discovery.chaining_faction_ids() == []
    end

    test "returns a faction once even with multiple AA keys", %{
      chain: chain,
      faction: faction,
      faction_position: faction_position
    } do
      user_id = unique_id()

      Repo.insert!(%Tornium.Schema.User{
        tid: user_id,
        name: "test user",
        faction_id: faction.tid,
        faction_position_id: faction_position.pid,
        faction_aa: true
      })

      Repo.insert!(%Tornium.Schema.TornKey{
        user_id: user_id,
        api_key: "apikey_#{user_id}",
        default: true,
        disabled: false,
        paused: false,
        access_level: :full
      })

      assert Discovery.chaining_faction_ids() == [{faction.tid, chain.chain_id}]
    end
  end

  describe "discovery loop" do
    test "starts a monitor for each discovered faction", %{chain: chain, faction: faction} do
      pid = start_discovery(discovery_interval: 60_000)

      send(pid, :discover)
      assert_receive {:started, started_id}
      assert started_id == {faction.tid, chain.chain_id}
    end

    test "keeps rediscovering at the configured interval" do
      start_discovery(discovery_interval: 10)

      assert_receive {:started, _}, 500
      assert_receive {:started, _}, 500
    end

    test "starts with default options" do
      assert Process.alive?(start_discovery([]))
    end
  end
end
