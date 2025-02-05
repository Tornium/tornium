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

  @spec handle_event(
          {:GUILD_MEMBER_ADD, {guild_id :: integer(), new_member :: Nostrum.Struct.Guild.Member.t()},
           Nostrum.Struct.WSState.t()}
        ) :: any()
  def handle_event({:GUILD_MEMBER_ADD, {guild_id, %Nostrum.Struct.Guild.Member{} = new_member}, _ws_state}) do
    Tornium.Guild.Verify.handle_on_join(guild_id, new_member)
    |> verification_jail_message(new_member)

    {:ok, user} = Nostrum.Cache.UserCache.get(new_member.user_id)
    Logger.info("#{user.username} [#{new_member.user_id}] has joined guild #{guild_id}")
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
    Nostrum.Api.create_message(server.verify_jail_channel, %{embeds: [embed]})
  end
end
