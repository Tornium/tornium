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

defmodule Tornium.Workers.OCTypeUpdate do
  @moduledoc """
  Update all OC and OC slot data.
  """

  use Oban.Worker,
    max_attempts: 3,
    priority: 0,
    queue: :faction_processing,
    tags: ["faction", "oc"],
    unique: [
      period: :infinity,
      fields: [:worker],
      states: :incomplete
    ]

  @impl Oban.Worker
  def perform(%Oban.Job{} = _job) do
    api_key = Tornium.User.Key.get_random!()

    query =
      Tornex.SpecQuery.new()
      |> Tornex.SpecQuery.put_path(Torngen.Client.Path.Torn.Organizedcrimes)
      |> Tornium.Schema.TornKey.put_key(api_key)

    response = Tornex.API.get(query)

    query
    |> Tornex.SpecQuery.parse(response)
    |> Map.fetch!(Torngen.Client.Path.Torn.Organizedcrimes)
    |> Map.fetch!(TornOrganizedCrimeResponse)
    |> Tornium.Schema.OrganizedCrimeType.upsert_all!()

    :ok
  end
end
