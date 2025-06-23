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

defmodule Tornium.Workers.OCTeamUpdate do
  @moduledoc """
  Assign and check OC teams for a faction.

  We can assume that there are at least one OC teams given the check performed in `Tornium.Workers.OCUpdate` validating this.

  1. Assign OC teams OCs if they don't have any OC assigned or if the current OC has ended/expired
  2. Perform OC team-related checks
  3. Send OC team-related messages depending on server configuration
  """

  require Logger
  alias Tornium.Repo
  import Ecto.Query

  use Oban.Worker,
    max_attempts: 3,
    priority: 0,
    queue: :faction_processing,
    tags: ["faction", "oc"],
    unique: [
      period: :infinity,
      keys: [:faction_tid],
      states: [:available, :executing, :retryable, :scheduled]
    ]

  @impl Oban.Worker
  def perform(
        %Oban.Job{
          args: %{
            "faction_tid" => faction_tid
          }
        } = _job
      )
      when is_integer(faction_tid) do
    crimes =
      Tornium.Schema.OrganizedCrime
      |> where([c], c.faction_id == ^faction_tid and c.status == :recruiting)
      |> join(:inner, [c], s in assoc(c, :slots), on: c.oc_id == s.oc_id)
      |> preload([c, s], slots: s)
      |> Repo.all()

    # This is necessary to retrieve the most recent OC assigned to each OC team.
    # Otherwise, the query is not guaranteed to use the most recent OC assigned.
    current_crime_query =
      Tornium.Schema.OrganizedCrime
      |> order_by([c], desc: c.assigned_team_at)
      |> distinct([c], c.assigned_team_id)

    %Tornium.Faction.OC.Team.Check.Struct{} =
      check_struct =
      Tornium.Schema.OrganizedCrimeTeam
      |> where([t], t.faction_id == ^faction_tid)
      |> join(:left, [t], m in assoc(t, :members), on: m.team_id == t.guid)
      |> join(:left, [t, m], c in subquery(current_crime_query), on: t.guid == c.assigned_team_id)
      |> join(:inner, [t, m, c], f in assoc(t, :faction), on: f.tid == t.faction_id)
      # New OC team and no OC assigned; OR
      # The current assigned OC has finished or has expired
      |> where(
        [t, m, c, f],
        is_nil(c.assigned_team_id) or not is_nil(c.executed_at) or ^DateTime.utc_now() >= c.expires_at
      )
      |> preload([t, m, c, f], members: m, faction: f)
      |> Repo.all()
      |> Tornium.Faction.OC.Team.reassign_teams(crimes)
      |> Tornium.Faction.OC.Team.Check.Struct.set_assigned_teams()
      |> Tornium.Faction.OC.Team.update_assigned_teams()

    config = Tornium.Schema.ServerOCConfig.get_by_faction(faction_tid)

    check_struct
    |> Tornium.Faction.OC.Team.Render.render_all(config)
    |> Tornium.Discord.send_messages()

    :ok
  end
end
