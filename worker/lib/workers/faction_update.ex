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

defmodule Tornium.Workers.FactionUpdate do
  @moduledoc """
  Update a faction's data in the database.

  The update is considered `nonpublic?` if the API key used for the update belongs to a member
  of the faction who has AA permissions. When `nonpublic?`, the update of the faction will also
  update its faction permissions and other private information if included in the API call
  response.

  If there is no API call ID, it is considered that the job must start it itself. This should
  only be the case when the worker is invoked from Python where it would be unable to perform
  the API call and store it in the Elixir node(s). In this case, the worker will schedule a
  new Oban job to update the faction data.
  """

  import Ecto.Query
  alias Tornium.Repo

  # This worker shouldn't have a unique section as it needs to be able to insert a child job when
  # invoked from outside of the Elixir worker.
  use Oban.Worker,
    max_attempts: 3,
    priority: 0,
    queue: :faction_processing,
    tags: ["faction"]

  @impl Oban.Worker
  def perform(%Oban.Job{
        args: %{
          "api_call_id" => nil,
          "api_key_id" => api_key_id,
          "faction_id" => faction_id,
          "user_id" => user_id,
          "nonpublic?" => nonpublic?
        }
      })
      when is_integer(faction_id) do
    # As it is not suggested to modify the database directly to update an Oban job, we are just going
    # to create a new Oban job and return it. If some process is waiting on the job to finish, it can
    # wait for that instead.
    %Tornium.Schema.TornKey{} =
      api_key =
      Tornium.Schema.TornKey
      |> where([k], k.guid == ^api_key_id and k.user_id == ^user_id)
      |> Repo.one()

    query = Tornium.Workers.FactionUpdateScheduler.faction_update_query(faction_id, api_key, nonpublic?)

    api_call_id = Ecto.UUID.generate()
    Tornium.API.Store.create(api_call_id, 300)

    Task.Supervisor.async_nolink(Tornium.TornexTaskSupervisor, fn ->
      query
      |> Tornex.Scheduler.Bucket.enqueue()
      |> Tornium.API.Store.insert(api_call_id)
    end)

    %{
      faction_id: faction_id,
      api_call_id: api_call_id,
      api_key_id: api_key_id,
      user_id: user_id,
      nonpublic?: nonpublic?
    }
    |> __MODULE__.new(schedule_in: _seconds = 15)
    |> Oban.insert()
  end

  @impl Oban.Worker
  def perform(
        %Oban.Job{
          args: %{
            "api_call_id" => api_call_id,
            "api_key_id" => api_key_id,
            "faction_id" => faction_id,
            "user_id" => user_id,
            "nonpublic?" => nonpublic?
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

      %{"error" => %{"code" => 2}} ->
        # The API key has been deleted so we can just delete the respective API key based upon the
        # primary key.
        # TODO: Switch to another API key if there is one available as a default.
        Tornium.Schema.TornKey
        |> where([k], k.guid == ^api_key_id)
        |> Repo.delete_all()

        {:cancel, {:api_error, 2}}

      %{"error" => %{"code" => error_code}} when error_code in [10, 13] ->
        # The owner of this API key has been inactive for over 7 days or is in federal jail so we
        # can just disable their API key as using it will be pointless. When/if the user returns,
        # they can enable it again.
        Tornium.Schema.TornKey
        |> where([k], k.user_id == ^user_id)
        |> update([k], set: [disabled: true])
        |> Repo.update_all([])

        {:cancel, {:api_error, error_code}}

      %{"error" => %{"code" => 18}} ->
        # The API key has been paused so we should pause the API key in the database by the pk
        # of the API key. When/if the user un-pauses their API key, we can enable it again.
        # TODO: Switch to another API key if there is one available as a default.
        Tornium.Schema.TornKey
        |> where([k], k.guid == ^api_key_id)
        |> update([k], set: [paused: true])
        |> Repo.update_all([])

        {:cancel, {:api_error, 18}}

      %{"error" => %{"code" => 7}} ->
        Tornium.Schema.User
        |> update([u], set: [faction_aa: false])
        |> where([u], u.tid == ^user_id and u.faction_id == ^faction_id)
        |> Repo.update_all([])

        Tornium.Workers.FactionUpdateScheduler.schedule_faction_update(faction_id, public?: true)

        :ok

      %{"error" => %{"code" => error_code}} when is_integer(error_code) ->
        {:cancel, {:api_error, error_code}}

      result when is_map(result) ->
        do_perform(result, nonpublic?)
    end
  end

  @doc false
  @spec do_perform(api_call_result :: map(), nonpublic? :: boolean()) :: Oban.Worker.result()
  def do_perform(api_call_result, true = _nonpublic?) when is_map(api_call_result) do
    %{
      Torngen.Client.Path.Faction.Basic => %{
        FactionBasicResponse => %Torngen.Client.Schema.FactionBasicResponse{
          basic: %Torngen.Client.Schema.FactionBasic{id: faction_id} = basic_data
        }
      },
      Torngen.Client.Path.Faction.Members => %{
        FactionMembersResponse => %Torngen.Client.Schema.FactionMembersResponse{members: members_data}
      },
      Torngen.Client.Path.Faction.Positions => %{
        FactionPositionsResponse => %Torngen.Client.Schema.FactionPositionsResponse{positions: positions_data}
      }
    } =
      Tornex.SpecQuery.new()
      |> Tornex.SpecQuery.put_path(Torngen.Client.Path.Faction.Basic)
      |> Tornex.SpecQuery.put_path(Torngen.Client.Path.Faction.Members)
      |> Tornex.SpecQuery.put_path(Torngen.Client.Path.Faction.Positions)
      |> Tornex.SpecQuery.parse(api_call_result)

    Tornium.Schema.Faction.upsert(basic_data)

    positions = Tornium.Schema.FactionPosition.upsert_all(positions_data, faction_id)
    members = Tornium.Schema.Faction.upsert_members(members_data, positions, faction_id)

    Tornium.Schema.Faction.strip_old_members(members, faction_id)
    Tornium.Schema.FactionPosition.remove_old_positions(positions, faction_id)

    :ok
  end

  def do_perform(api_call_result, false = _nonpublic?) when is_map(api_call_result) do
    %{
      Torngen.Client.Path.Faction.Id.Basic => %{
        FactionBasicResponse => %Torngen.Client.Schema.FactionBasicResponse{
          basic: %Torngen.Client.Schema.FactionBasic{id: faction_id} = basic_data
        }
      },
      Torngen.Client.Path.Faction.Id.Members => %{
        FactionMembersResponse => %Torngen.Client.Schema.FactionMembersResponse{members: members_data}
      }
    } =
      Tornex.SpecQuery.new()
      |> Tornex.SpecQuery.put_path(Torngen.Client.Path.Faction.Id.Basic)
      |> Tornex.SpecQuery.put_path(Torngen.Client.Path.Faction.Id.Members)
      |> Tornex.SpecQuery.parse(api_call_result)

    Tornium.Schema.Faction.upsert(basic_data)

    positions =
      Tornium.Schema.FactionPosition
      |> where([p], p.faction_id == ^faction_id)
      |> Repo.all()

    members_data
    |> Tornium.Schema.Faction.upsert_members(positions, faction_id)
    |> Tornium.Schema.Faction.strip_old_members(faction_id)

    :ok
  end
end
