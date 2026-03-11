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
  @moduledoc """
  Upsert organized crime CPR data from faction OCs in the `Recruiting` status.
  """

  use Oban.Worker,
    max_attempts: 3,
    priority: 9,
    queue: :user_processing,
    tags: ["user", "oc"]

  @impl Oban.Worker
  def perform(
        %Oban.Job{
          args: %{
            "user_tid" => user_id,
            "faction_tid" => faction_id,
            "api_call_id" => api_call_id
          }
        } = _job
      ) do
    api_call_id
    |> Tornium.API.Store.pop()
    |> handle_response(user_id, faction_id)
  end

  @impl Oban.Worker
  def timeout(%Oban.Job{} = _job) do
    :timer.seconds(5)
  end

  @spec handle_response(
          response :: map() | :not_ready | :expired | nil,
          user_id :: pos_integer(),
          faction_id :: pos_integer()
        ) :: Oban.Worker.result()
  def handle_response(response, _user_id, _faction_id) when is_nil(response) do
    {:cancel, :invalid_call_id}
  end

  def handle_response(:expired = _response, _user_id, _faction_id) do
    {:cancel, :expired}
  end

  def handle_response(:not_ready = _response, _user_id, _faction_id) do
    # This uses :error instead of :snooze to allow for an easy cap on the number of retries
    {:error, :not_ready}
  end

  def handle_response(%{"error" => %{"code" => error_code}}, _user_id, _faction_id) when is_integer(error_code) do
    {:cancel, {:api_error, error_code}}
  end

  def handle_response(response, user_id, faction_id)
      when is_map(response) and is_integer(user_id) and is_integer(faction_id) do
    now = DateTime.utc_now() |> DateTime.truncate(:second)
    query = Tornex.SpecQuery.put_path(Tornex.SpecQuery.new(), Torngen.Client.Path.User.Organizedcrimes)

    %{
      Torngen.Client.Path.User.Organizedcrimes => %{
        UserOrganizedCrimesResponse => %Torngen.Client.Schema.UserOrganizedCrimesResponse{
          organizedcrimes: crimes
        }
      }
    } = Tornex.SpecQuery.parse(query, response)

    crimes
    |> Enum.sort_by(fn %Torngen.Client.Schema.FactionCrime{created_at: created_at} -> created_at end, :desc)
    |> Enum.flat_map(fn %Torngen.Client.Schema.FactionCrime{name: oc_name, slots: slots} ->
      # The slots data in this API response only lists unfilled slots
      slots
      |> Enum.map(fn %Torngen.Client.Schema.FactionCrimeSlot{position: slot_position, checkpoint_pass_rate: slot_cpr} ->
        %Tornium.Schema.OrganizedCrimeCPR{
          guid: Ecto.UUID.generate(),
          oc_name: oc_name,
          oc_position: slot_position,
          cpr: slot_cpr,
          user_id: user_id,
          updated_at: now
        }
      end)
    end)
    |> Enum.uniq_by(fn %Tornium.Schema.OrganizedCrimeCPR{oc_name: oc_name, oc_position: oc_position} ->
      {oc_name, oc_position}
    end)
    |> Tornium.Schema.OrganizedCrimeCPR.upsert_all()

    :ok
  end
end
