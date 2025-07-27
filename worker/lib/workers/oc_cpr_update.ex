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

defmodule Tornium.Workers.OCCPRUpdate do
  require Logger

  use Oban.Worker,
    max_attempts: 3,
    priority: 9,
    queue: :user_processing,
    tags: ["user", "oc"],
    unique: [
      period: :infinity,
      keys: [:api_call_id],
      states: [:available, :executing, :retryable, :scheduled]
    ]

  @impl Oban.Worker
  def perform(
        %Oban.Job{
          args: %{
            "user_tid" => user_tid,
            "faction_tid" => faction_tid,
            "api_call_id" => api_call_id
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

      %{} = result ->
        now = DateTime.utc_now() |> DateTime.truncate(:second)

        result
        |> Tornium.Faction.OC.parse(faction_tid)
        |> Enum.sort_by(fn %Tornium.Schema.OrganizedCrime{created_at: created_at} -> created_at end, :desc)
        |> Enum.uniq_by(fn %Tornium.Schema.OrganizedCrime{oc_name: oc_name} -> oc_name end)
        |> flatten_crimes()
        |> Enum.map(fn %Tornium.Schema.OrganizedCrimeCPR{} = cpr ->
          %Tornium.Schema.OrganizedCrimeCPR{cpr | user_id: user_tid, updated_at: now}
        end)
        |> Tornium.Schema.OrganizedCrimeCPR.upsert_all()

        :ok
    end
  end

  @impl Oban.Worker
  def timeout(%Oban.Job{} = _job) do
    :timer.seconds(5)
  end

  @spec flatten_crimes(crimes :: [Tornium.Schema.OrganizedCrime.t()], acc :: [Tornium.Schema.OrganizedCrimeCPR.t()]) ::
          [Tornium.Schema.OrganizedCrimeCPR.t()]
  defp flatten_crimes(crimes, acc \\ [])

  defp flatten_crimes([%Tornium.Schema.OrganizedCrime{oc_name: oc_name, slots: slots} | remaining_crimes], acc) do
    slot_cpr =
      slots
      |> Enum.uniq_by(fn %Tornium.Schema.OrganizedCrimeSlot{crime_position: position} -> position end)
      |> Enum.map(fn %Tornium.Schema.OrganizedCrimeSlot{crime_position: position, user_success_chance: cpr} ->
        %Tornium.Schema.OrganizedCrimeCPR{
          guid: Ecto.UUID.generate(),
          oc_name: oc_name,
          oc_position: position,
          cpr: cpr
        }
      end)
      |> Enum.concat(acc)

    flatten_crimes(remaining_crimes, slot_cpr)
  end

  defp flatten_crimes([], acc) do
    acc
  end
end
