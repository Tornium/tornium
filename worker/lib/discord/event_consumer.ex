# Copyright (C) 2021-2023 tiksan
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
    verification_result = Tornium.Guild.Verify.handle(guild_id, new_member)

    case verification_result do
      {:error, :api_key, _} ->
        nil

      {:error, :exclusion_role, _} ->
        nil

      {:error, {:config, _}, _} ->
        nil

      {status_atom, result, %Tornium.Schema.Server{} = guild} ->
        # TODO: Rename the message method
        # TODO: Validate jail channel before sending message
        # TODO: Clean up jail channel message sending
        embed = Tornium.Guild.Verify.Message.message({status_atom, result}, new_member)
        IO.inspect(embed)
        Nostrum.Api.create_message(guild.verify_jail_channel, %{embeds: [embed]}) |> IO.inspect()
    end

    {:ok, user} = Nostrum.Cache.UserCache.get(new_member.user_id)
    Logger.info("#{user.username} [#{new_member.user_id}] has joined guild #{guild_id}")
    nil
  end
end
