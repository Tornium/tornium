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

defmodule Tornium.Workers.ArmoryNewsUpdate do
  @moduledoc """
  Insert new armory news events.
  """

  import Ecto.Query
  alias Tornium.Repo

  use Oban.Worker,
    max_attempts: 3,
    priority: 0,
    queue: :faction_processing,
    tags: ["faction"],
    unique: [
      period: :infinity,
      fields: [:worker, :args],
      keys: [:api_call_id],
      states: :incomplete
    ]

  @armory_news_category "armoryAction"

  @impl Oban.Worker
  def perform(
        %Oban.Job{
          args: %{
            "api_call_id" => api_call_id,
            "faction_id" => faction_id
          }
        } = _job
      ) do
    case Tornium.API.Store.pop(api_call_id) do
      nil ->
        {:cancel, :invalid_call_id}

      :expired ->
        {:cancel, :expired}

      :not_ready ->
        # This uses :error instead of :snooze to allow for an easy cap on the number of retries
        {:error, :not_ready}

      result when is_map(result) ->
        do_perform(result, faction_id)
    end
  end

  @spec do_perform(api_call_result :: map(), faction_id :: non_neg_integer()) :: Oban.Worker.result()
  def do_perform(api_call_result, faction_id) when is_map(api_call_result) and is_integer(faction_id) do
    %{
      Torngen.Client.Path.Faction.News => %{
        FactionNewsResponse => %Torngen.Client.Schema.FactionNewsResponse{news: armory_usage_news}
      }
    } =
      Tornex.SpecQuery.new()
      |> Tornex.SpecQuery.put_path(Torngen.Client.Path.Faction.News)
      |> Tornex.SpecQuery.put_parameter(:cat, @armory_news_category)
      |> Tornex.SpecQuery.parse(api_call_result)

    @armory_news_category
    |> Tornium.Faction.News.parse(armory_usage_news)
    |> Tornium.Schema.ArmoryUsage.insert_all(faction_id)

    if length(armory_usage_news) == 100 do
      # If the length of the news is 100, it can be assumed that there are more logs than what was returned
      # as the maximum and default `limit` is 100.
      Tornium.Workers.ArmoryNewsUpdateScheduler.schedule_faction(faction_id)
    end

    :ok
  end

  @impl Oban.Worker
  def timeout(%Oban.Job{} = _job) do
    :timer.minutes(1)
  end
end
