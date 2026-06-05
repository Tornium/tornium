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

defmodule Tornium.Workers.UserUpdate do
  use Oban.Worker,
    max_attempts: 3,
    priority: 0,
    queue: :faction_processing,
    tags: ["faction"]

  @impl Oban.Worker
  def perform(
        %Oban.Job{
          args: %{
            "api_call_id" => api_call_id,
            "user_id" => _user_id
          }
        } = _job
      )
      when is_nil(api_call_id) do
    # TODO: Implement this to perform the API call and update API call ID (similar to the schedule function)
    {:cancel, :not_yet_implemented}
  end

  def perform(
        %Oban.Job{
          args: %{
            "api_call_id" => api_call_id,
            "user_id" => user_id,
            "api_key_owner" => api_key_owner
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

      %{"error" => %{"code" => error_code}} when is_integer(error_code) ->
        {:cancel, {:api_error, error_code}}

      response when is_map(response) ->
        api_key = Tornium.User.Key.get_by_user(api_key_owner)

        Tornium.User.update_query(user_id, api_key)
        |> Tornex.SpecQuery.parse(response)
        |> Tornium.User.update_data()
    end
  end
end
