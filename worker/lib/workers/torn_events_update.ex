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

defmodule Tornium.Workers.TornEventsUpdate do
  @moduledoc """
  Upsert all official Torn events from the API to the database.
  """

  use Oban.Worker,
    max_attempts: 3,
    priority: 0,
    queue: :miscellaneous,
    tags: ["calendar"],
    unique: [
      period: :infinity,
      fields: [:worker],
      states: :incomplete
    ]

  @impl Oban.Worker
  def perform(%Oban.Job{} = _job) do
    query = Tornium.User.Key.get_random!() |> query(nice: -10)

    response = Tornex.Scheduler.Bucket.enqueue(query)

    %{
      Torngen.Client.Path.Torn.Calendar => %{
        TornCalendarResponse => %Torngen.Client.Schema.TornCalendarResponse{
          calendar: %{
            events: events,
            competitions: competitions
          }
        }
      }
    } = Tornex.SpecQuery.parse(query, response)

    parsed_events = Enum.map(events, &Tornium.Schema.TornEvent.parse(&1, :event))
    parsed_competitions = Enum.map(competitions, &Tornium.Schema.TornEvent.parse(&1, :competition))

    Tornium.Schema.TornEvent.upsert_all(parsed_events ++ parsed_competitions)

    :ok
  end

  @doc false
  @spec query(api_key :: Tornium.Schema.TornKey.t(), opts :: keyword()) :: Tornex.SpecQuery.t()
  def query(%Tornium.Schema.TornKey{} = api_key, opts \\ []) do
    Tornex.SpecQuery.new(opts)
    |> Tornex.SpecQuery.put_path(Torngen.Client.Path.Torn.Calendar)
    |> Tornium.Schema.TornKey.put_key(api_key)
  end
end
