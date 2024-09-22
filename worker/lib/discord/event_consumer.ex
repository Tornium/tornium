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
    Tornium.Guild.Verify.handle(guild_id, new_member) |> IO.inspect()
    {:ok, user} = Nostrum.Cache.UserCache.get(new_member.user_id)

    Logger.info("#{user.username} [#{new_member.user_id}] has joined guild #{guild_id}")
    nil
  end
end
