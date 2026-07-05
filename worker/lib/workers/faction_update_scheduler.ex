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

defmodule Tornium.Workers.FactionUpdateScheduler do
  @moduledoc """
  A scheduler to spawn `Tornium.Workers.FactionUpdate` for the `@max_chunk` least recently updated
  factions.
  """

  import Ecto.Query
  alias Tornium.Repo

  use Oban.Worker,
    max_attempts: 3,
    priority: 0,
    queue: :scheduler,
    tags: ["scheduler", "faction"],
    unique: [
      period: :infinity,
      fields: [:worker],
      states: :incomplete
    ]

  @max_chunk if Application.compile_env!(:tornium, :env) == :dev, do: 5, else: 100

  @impl Oban.Worker
  def perform(%Oban.Job{} = _job) do
    # TODO: Change f.last_members to the more traditional f.updated_at
    one_hour_ago = DateTime.utc_now() |> DateTime.add(-1, :hour)

    valid_aa_key_subquery =
      Tornium.Schema.TornKey
      |> where([k], k.default == true and k.disabled == false and k.paused == false and k.access_level >= :limited)
      |> join(:inner, [k], u in assoc(k, :user), on: u.tid == k.user_id)
      |> where([k, u], not is_nil(u.faction_id) and u.faction_id == parent_as(:faction).tid and u.faction_aa == true)

    high_priority_factions =
      Tornium.Schema.Faction
      |> from(as: :faction)
      |> where([f], (is_nil(f.last_members) or f.last_members < ^one_hour_ago) and exists(valid_aa_key_subquery))
      |> order_by([f], asc_nulls_first: f.last_members)
      |> limit(@max_chunk)
      |> Repo.all()

    remaining_limit = @max_chunk - length(high_priority_factions)

    other_factions =
      if remaining_limit > 0 do
        high_priority_faction_ids = Enum.map(high_priority_factions, & &1.tid)

        Tornium.Schema.Faction
        |> where(
          [f],
          f.tid not in ^high_priority_faction_ids and (is_nil(f.last_members) or f.last_members < ^one_hour_ago)
        )
        |> order_by([f], asc_nulls_first: f.last_members)
        |> limit(^remaining_limit)
        |> Repo.all()
      else
        []
      end

    Enum.each(high_priority_factions ++ other_factions, &schedule_faction_update/1)

    :ok
  end

  @doc """
  Schedule a specific faction's data be updated.

  ## Options
    * `:public?` - Only collect public data regardless of the API key available (default: `false`)
  """
  @spec schedule_faction_update(
          faction :: Tornium.Schema.Faction.t() | pos_integer(),
          opts :: keyword()
        ) :: {:ok, Oban.Job.t()} | {:error, Oban.Job.changeset() | term()}
  def schedule_faction_update(faction, opts \\ [])

  def schedule_faction_update(faction, opts) when is_integer(faction) do
    Tornium.Schema.Faction
    |> where([f], f.tid == ^faction)
    |> first()
    |> Repo.one!()
    |> schedule_faction_update(opts)
  end

  def schedule_faction_update(%Tornium.Schema.Faction{tid: faction_id} = faction, opts) when is_integer(faction_id) do
    # If there is no faction AA API key available to use for this API call, it will set `:nonpublic?` to false
    # to indicate that the API call can only make and parse public selections. This allows for all factions to
    # be regularly updated instead of only those factions that have AA keys.
    {%Tornium.Schema.TornKey{guid: api_key_id, user_id: key_owner} = key, nonpublic?} = api_key(faction)

    force_public? = Keyword.get(opts, :public?, false)
    query = faction_update_query(faction_id, key, nonpublic? and not force_public?)

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
      user_id: key_owner,
      nonpublic?: nonpublic? and not force_public?
    }
    |> Tornium.Workers.FactionUpdate.new(schedule_in: _seconds = 15)
    |> Oban.insert()
  end

  @doc false
  @spec faction_update_query(
          faction_id :: pos_integer(),
          api_key :: Tornium.Schema.TornKey.t() | String.t(),
          nonpublic? :: boolean()
        ) :: Tornex.SpecQuery.t()
  def faction_update_query(faction_id, %Tornium.Schema.TornKey{} = api_key, true = _nonpublic?)
      when is_integer(faction_id) do
    Tornex.SpecQuery.new(nice: 10, resource_id: faction_id)
    |> Tornium.Schema.TornKey.put_key(api_key)
    |> Tornex.SpecQuery.put_path(Torngen.Client.Path.Faction.Basic)
    |> Tornex.SpecQuery.put_path(Torngen.Client.Path.Faction.Members)
    |> Tornex.SpecQuery.put_path(Torngen.Client.Path.Faction.Positions)
  end

  def faction_update_query(faction_id, %Tornium.Schema.TornKey{} = api_key, false = _nonpublic?)
      when is_integer(faction_id) do
    Tornex.SpecQuery.new(nice: 10, resource_id: faction_id)
    |> Tornium.Schema.TornKey.put_key(api_key)
    |> Tornex.SpecQuery.put_path(Torngen.Client.Path.Faction.Id.Basic)
    |> Tornex.SpecQuery.put_path(Torngen.Client.Path.Faction.Id.Members)
    |> Tornex.SpecQuery.put_parameter!(:id, faction_id)
  end

  @spec api_key(faction :: Tornium.Schema.Faction.t()) :: {Tornium.Schema.TornKey.t(), boolean()}
  defp api_key(%Tornium.Schema.Faction{tid: faction_id, leader_id: leader_id, coleader_id: coleader_id} = _faction) do
    case Tornium.Faction.get_key(faction_id) do
      %Tornium.Schema.TornKey{default: true, disabled: false, paused: false, access_level: access_level} = aa_key
      when access_level in [:limited, :full] ->
        {aa_key, true}

      _ ->
        # TODO: Clean up these nested cases

        # Sometimes, there will not be any faction positions but the leader/coleader of the faction will be set and will
        # have an API key. We should attempt to use their API key so that we can get the faction positions and set their
        # `:faction_aa` value. If the leader/coleader is not signed in, we should fallback to a random API key.
        leadership_key = Tornium.User.Key.get_by_user(leader_id) || Tornium.User.Key.get_by_user(coleader_id)

        case leadership_key do
          %Tornium.Schema.TornKey{default: true, disabled: false, paused: false, access_level: access_level}
          when access_level in [:limited, :full] ->
            {leadership_key, true}

          nil ->
            # TODO: Convert this to use some sort of circular buffer with Tornium.User.Key.get_random/1 so
            # that there only needs to be 1 DB call
            {Tornium.User.Key.get_random!(), false}
        end
    end
  end
end
