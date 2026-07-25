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

defmodule Tornium.Test.FactionUpdate do
  use Tornium.RepoCase, async: false

  @api_key Application.compile_env(:tornium, :api_key)

  @tag :integration
  test "update self faction" do
    query =
      Tornex.SpecQuery.new(nice: -20, resource_id: 0)
      |> Tornex.SpecQuery.put_key(@api_key)
      |> Tornex.SpecQuery.put_path(Torngen.Client.Path.Faction.Basic)
      |> Tornex.SpecQuery.put_path(Torngen.Client.Path.Faction.Members)
      |> Tornex.SpecQuery.put_path(Torngen.Client.Path.Faction.Positions)

    response = Tornex.API.get(query)
    faction_id = response |> Map.fetch!("basic") |> Map.fetch!("id")
    assert :ok = Tornium.Workers.FactionUpdate.do_perform(response, faction_id, true)

    members =
      Tornium.Schema.User
      |> where([u], u.faction_id == ^faction_id)
      |> Repo.all()

    assert length(members) == response |> Map.fetch!("members") |> length()

    positions =
      Tornium.Schema.FactionPosition
      |> where([p], p.faction_id == ^faction_id)
      |> Repo.all()

    assert length(positions) == response |> Map.fetch!("positions") |> length() |> Kernel.+(3)
  end

  @tag :integration
  test "update other faction" do
    faction_id = 19

    query =
      Tornex.SpecQuery.new(nice: -20, resource_id: faction_id)
      |> Tornex.SpecQuery.put_key(@api_key)
      |> Tornex.SpecQuery.put_path(Torngen.Client.Path.Faction.Id.Basic)
      |> Tornex.SpecQuery.put_path(Torngen.Client.Path.Faction.Id.Members)
      |> Tornex.SpecQuery.put_parameter!(:id, faction_id)

    response = Tornex.API.get(query)
    assert :ok = Tornium.Workers.FactionUpdate.do_perform(response, faction_id, false)

    members =
      Tornium.Schema.User
      |> where([u], u.faction_id == ^faction_id)
      |> Repo.all()

    assert length(members) == response |> Map.fetch!("members") |> length()
  end
end
