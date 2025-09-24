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

defmodule Tornium.Workers.OverdoseDailyReport do
  @moduledoc """
  Send a daily report for a faction's overdoses.

  For every faction that has a overdose reporting policy set to `:daily`, a embed reporting the faction's overdoses
  during that period will be generated and sent to the set channel.
  """

  alias Tornium.Repo
  import Ecto.Query

  use Oban.Worker,
    max_attempts: 3,
    priority: 0,
    queue: :faction_processing,
    tags: ["faction"],
    unique: [
      period: :infinity,
      fields: [:worker],
      states: :incomplete
    ]

  @impl Oban.Worker
  def perform(%Oban.Job{} = _job) do
    Tornium.Schema.OverdoseEvent
    |> where([e], is_nil(e.notified_at))
    |> join(:inner, [e], f in assoc(e, :faction))
    |> join(:inner, [e, f], s in assoc(f, :guild))
    |> where([e, f, s], f.tid in s.factions)
    |> Repo.all()
    |> Enum.group_by(fn %Tornium.Schema.OverdoseEvent{faction_id: faction_id} -> faction_id end)
    |> Enum.each(fn {faction_id, overdose_events} when is_list(overdose_events) ->
      faction_id
      |> Tornium.Schema.ServerOverdoseConfig.get_by_faction()
      |> send_report(faction_id, overdose_events)
    end)

    :ok
  end

  @spec send_report(
          config :: Tornium.Schema.ServerOverdoseConfig.t(),
          faction_id :: integer(),
          overdose_events :: [Tornium.Schema.OverdoseEvent.t()]
        ) :: nil
  def send_report(
        %Tornium.Schema.ServerOverdoseConfig{policy: "daily", channel: channel} = _config,
        faction_id,
        overdose_events
      )
      when is_integer(faction_id) and is_list(overdose_events) and is_integer(channel) and channel != 0 do
    %Tornium.Schema.Faction{name: faction_name} =
      Tornium.Schema.Faction
      |> select([f], f.name)
      |> where([f], f.tid == ^faction_id)
      |> Repo.one()

    overdose_events
    |> Repo.preload(:user)
    |> Tornium.Faction.Overdose.to_report_embed(faction_name)
    |> List.wrap()
    |> Tornium.Discord.send_messages()

    Tornium.Schema.OverdoseEvent.notify_all(overdose_events)
  end

  def send_report(_config, _faction_id, _overdose_events) do
    nil
  end
end
