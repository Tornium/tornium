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

defmodule Tornium.Workers.OCMissingMemberNotifications do
  @moduledoc """
  Notifications for factions with members who should be in an OC but aren't. 
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
      fields: [:worker],
      states: :incomplete
    ]

  @impl Oban.Worker
  def perform(%Oban.Job{} = _job) do
    Tornium.Schema.ServerOCConfig
    |> where([c], not is_nil(c.missing_member_channel) and c.missing_member_channel != 0)
    |> join(:inner, [c], s in assoc(c, :server), on: c.server_id == s.sid)
    |> where([c, s], c.faction_id in s.factions)
    |> join(:inner, [c, s], f in assoc(c, :faction), on: c.faction_id == f.tid)
    |> where(
      [c, s, f],
      f.guild_id == s.sid and f.has_migrated_oc == true and
        ^DateTime.utc_now() - f.last_members < ^Duration.new!(day: 1)
    )
    |> select([c, s, f], [c.missing_member_channel, c.missing_member_roles, c.missing_member_minimum_duration, f.tid])
    |> Repo.all()
    |> IO.inspect()
    |> Enum.each(fn [missing_member_channel, missing_member_roles, missing_member_minimum_duration, faction_id] ->
      latest_oc_subquery =
        Tornium.Schema.OrganizedCrimeSlot
        |> join(:inner, [s], c in assoc(s, :oc), on: s.oc_id == c.oc_id)
        |> where([s, c], c.faction_id == ^faction_id)
        |> order_by([s, c], asc: s.user_id, desc: c.ready_at)
        |> distinct([s, c], s.user_id)
        |> select([s, c], %{
          oc_id: c.oc_id,
          executed_at: c.executed_at,
          user_id: s.user_id,
          faction_id: c.faction_id
        })

      faction_name =
        Tornium.Schema.Faction
        |> select([f], f.name)
        |> where([f], f.tid == ^faction_id)
        |> first()
        |> Repo.one()

      Tornium.Schema.User
      |> where([u], u.faction_id == ^faction_id)
      |> join(:left, [u], oc in subquery(latest_oc_subquery), on: oc.user_id == u.tid and oc.faction_id == u.faction_id)
      |> where(
        [u, oc],
        is_nil(oc.user_id) or
          (not is_nil(oc.executed_at) and ^DateTime.utc_now() - oc.executed_at > ^missing_member_minimum_duration)
      )
      |> select([u, oc], %{
        user_id: u.tid,
        user_name: u.name,
        user_discord_id: u.discord_id,
        user_faction_name: ^faction_name,
        last_oc_id: oc.oc_id,
        last_oc_executed_at: oc.executed_at
      })
      |> Repo.all()
      |> IO.inspect()
      |> Enum.map(fn missing_member when is_map(missing_member) ->
        generate_message(missing_member, missing_member_channel, missing_member_roles)
      end)
      |> Tornium.Discord.send_messages(collect: true)
      |> IO.inspect()
    end)

    :ok
  end

  @spec generate_message(
          missing_member :: map(),
          channel_id :: pos_integer(),
          roles :: [Tornium.Discord.role_assignable()]
        ) :: Nostrum.Struct.Message.t()
  defp generate_message(
         %{
           user_id: user_id,
           user_name: user_name,
           user_discord_id: user_discord_id,
           user_faction_name: user_faction_name,
           last_oc_id: last_oc_id,
           last_oc_executed_at: %DateTime{} = last_oc_executed_at
         },
         channel_id,
         roles
       )
       when is_integer(channel_id) and channel_id != 0 and is_list(roles) do
    %Nostrum.Struct.Message{
      channel_id: channel_id,
      content: Tornium.Discord.roles_to_string(roles, assigns: [{:user, user_discord_id}]),
      embeds: [
        %Nostrum.Struct.Embed{
          title: "Member OC Join Required",
          description:
            "#{user_faction_name} member [#{user_name} [#{user_id}]](https://www.torn.com/profiles.php?XID=#{user_id}) was last in an oc <t:#{DateTime.to_unix(last_oc_executed_at)}:R> (OC ID [#{last_oc_id}](https://www.torn.com/factions.php?step=your&type=1#/tab=crimes&crimeId=#{last_oc_id})) and needs to join an organized crime.",
          color: Tornium.Discord.Constants.colors()[:warning]
        }
      ]
    }
  end

  @impl Oban.Worker
  def timeout(%Oban.Job{} = _job) do
    :timer.minutes(1)
  end
end
