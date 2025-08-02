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

defmodule Tornium.Discord.Consumer do
  require Logger
  use Nostrum.Consumer
  import Ecto.Query
  alias Tornium.Repo

  @spec handle_event(event :: Nostrum.Consumer.guild_member_add()) :: term()
  def handle_event({:GUILD_MEMBER_ADD, {guild_id, %Nostrum.Struct.Guild.Member{} = new_member}, _ws_state}) do
    guild_id
    |> Tornium.Guild.Verify.handle_on_join(new_member)
    |> verification_jail_message(new_member)

    {:ok, user} = Nostrum.Cache.UserCache.get(new_member.user_id)
    Logger.info("#{user.username} [#{new_member.user_id}] has joined guild #{guild_id}")
    nil
  end

  @spec handle_event(event :: Nostrum.Consumer.guild_create()) :: term()
  def handle_event({
        :GUILD_CREATE,
        %Nostrum.Struct.Guild{id: guild_id, name: guild_name, owner_id: guild_owner_id, roles: roles} = _new_guild,
        _ws_state
      }) do
    :telemetry.execute([:tornium, :bot, :guild_joined], %{}, %{
      guild_id: guild_id,
      guild_name: guild_name
    })

    Tornium.Schema.Server.new(guild_id, guild_name)

    guild_admins_discord_ids =
      guild_id
      |> Tornium.Guild.fetch_admins(roles)
      |> List.insert_at(0, guild_owner_id)
      |> Enum.uniq()

    guild_admins =
      Tornium.Schema.User
      |> where([u], u.discord_id in ^guild_admins_discord_ids)
      |> select([u], u.tid)
      |> Repo.all()

    Tornium.Schema.Server
    |> update([s], set: [admins: ^guild_admins])
    |> where([s], s.sid == ^guild_id)
    |> Repo.update_all([])

    nil
  end

  @spec verification_jail_message(
          {:ok, Nostrum.Struct.Guild.Member.t(), Tornium.Schema.Server.t()}
          | {:error,
             Nostrum.Error.ApiError
             | Tornium.API.Error
             | :unverified
             | :nochanges
             | :api_key
             | :exclusion_role
             | {:config, String.t()}, Tornium.Schema.Server.t()},
          Nostrum.Struct.Guild.Member.t()
        ) :: nil
  defp verification_jail_message({:error, :api_key}, _) do
    nil
  end

  defp verification_jail_message({:error, :exclusion_role}, _) do
    nil
  end

  defp verification_jail_message({:error, {:config, _}}, _) do
    nil
  end

  defp verification_jail_message(
         {_, _, %Tornium.Schema.Server{verify_jail_channel: verify_jail_channel} = _server},
         _new_member
       )
       when verify_jail_channel == 0 or is_nil(verify_jail_channel) do
  end

  defp verification_jail_message({status_atom, result, server}, new_member) do
    # TODO: Rename the message method
    # TODO: Provide reasons for skipping certain errors
    embed = Tornium.Guild.Verify.Message.message({status_atom, result}, new_member)
    Nostrum.Api.Message.create(server.verify_jail_channel, %{embeds: [embed]})
  end
end
