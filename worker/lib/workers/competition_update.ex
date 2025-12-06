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

defmodule Tornium.Workers.CompetitionUpdate do
  @moduledoc """
  Update the overall data for a competition.

  This is non user-specific data from `torn/competition`.
  """

  use Oban.Worker,
    max_attempts: 3,
    priority: 5,
    queue: :scheduler,
    tags: ["torn"],
    unique: [
      period: :infinity,
      fields: [:worker],
      states: :incomplete
    ]

  @impl Oban.Worker
  def perform(%Oban.Job{} = _job) do
    %Tornium.Schema.TornKey{api_key: api_key, user_id: api_key_owner} = Tornium.User.Key.get_random_key()

    %Tornex.Query{resource: "torn", key: api_key, selections: ["competition"], key_owner: api_key_owner, nice: 0} |> Tornex.API.get() |> handle_competition_data()

    :ok
  end

  @impl Oban.Worker
  def timeout(%Oban.Job{} = _job) do
    # This condition should never happen but is here for stability
    :timer.minutes(1)
  end

  def handle_competition_data(data) do
    case data do
      %{"competition" => %{"name" => "Elimination", "teams" => elimination_teams}} ->
        Tornium.Elimination.update_teams(elimination_teams)

      _ ->
        nil
    end
  end
end
