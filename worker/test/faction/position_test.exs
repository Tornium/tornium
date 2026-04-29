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

defmodule Tornium.Test.FactionPosition do
  use Tornium.RepoCase, async: false

  @api_key Application.compile_env(:tornium, :api_key)

  test "position mapping" do
    mapped_position =
      Tornium.Schema.FactionPosition.map(
        %Torngen.Client.Schema.FactionPosition{
          name: "Member",
          is_default: true,
          abilities: ["Medical Usage", "Booster Usage"]
        },
        1
      )

    assert %Tornium.Schema.FactionPosition{
             name: "Member",
             faction_id: 1,
             default: true,
             permissions: ["Medical Usage", "Booster Usage"]
           } = mapped_position
  end

  @tag :integration
  test "position insertion from API data" do
    query =
      Tornex.SpecQuery.new(nice: 10)
      |> Tornex.SpecQuery.put_key(@api_key)
      |> Tornex.SpecQuery.put_path(Torngen.Client.Path.Faction.Positions)

    %{
      Torngen.Client.Path.Faction.Positions => %{
        FactionPositionsResponse => %Torngen.Client.Schema.FactionPositionsResponse{positions: positions_data}
      }
    } = Tornex.SpecQuery.parse(query, Tornex.API.get(query))

    %Tornium.Schema.Faction{tid: 1, name: "Test"} |> Repo.insert!()

    inserted_positions = Tornium.Schema.FactionPosition.upsert_all(positions_data, 1)
    assert length(inserted_positions) == length(positions_data)
  end

  test "duplicte position upsertion" do
    %Tornium.Schema.Faction{tid: 1, name: "Test"} |> Repo.insert!()

    pid = Ecto.UUID.generate()

    %Tornium.Schema.FactionPosition{
      pid: pid,
      name: "test",
      faction_id: 1,
      default: true,
      permissions: ["Medical Usage"]
    }
    |> Repo.insert!()

    Tornium.Schema.FactionPosition.upsert_all(
      [%Torngen.Client.Schema.FactionPosition{name: "test", is_default: false, abilities: ["Drug Usage"]}],
      1
    )

    positions = Repo.all(Tornium.Schema.FactionPosition)
    assert length(positions) == 1

    assert [%Tornium.Schema.FactionPosition{pid: ^pid, name: "test", default: false, permissions: ["Drug Usage"]}] =
             positions
  end

  test "old position removal" do
    %Tornium.Schema.Faction{tid: 1, name: "Test"} |> Repo.insert!()

    pid = Ecto.UUID.generate()

    %Tornium.Schema.FactionPosition{
      pid: pid,
      name: "test",
      faction_id: 1,
      default: true,
      permissions: ["Medical Usage"]
    }
    |> Repo.insert!()

    Repo.insert!(%Tornium.Schema.User{tid: 1, faction_id: 1, faction_position_id: pid, faction_aa: true})
    Tornium.Schema.FactionPosition.remove_old_positions([], 1)

    positions = Repo.all(Tornium.Schema.FactionPosition)
    assert [] = positions

    users = Repo.all(Tornium.Schema.User)
    assert length(users) == 1
    assert [%Tornium.Schema.User{tid: 1, faction_id: 1, faction_position_id: nil, faction_aa: false}] = users
  end
end
