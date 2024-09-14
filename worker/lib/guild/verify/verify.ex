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

defmodule Tornium.Guild.Verify do
  require Logger

  @spec handle(guild_id :: integer(), user :: Nostrum.Struct.User.t(), member :: Nostrum.Struct.Guild.Member.t()) :: nil
  def handle(guild_id, _user, member) do
    case Tornium.Guild.Verify.Config.validate(guild_id) do
      _config ->
        Tornex.Scheduler.Bucket.enqueue(%Tornex.Query{
          resource: "user",
          resource_id: member.user_id,
          selections: "profile",
          key: Enum.random(Tornium.Guild.get_admin_keys(guild_id)),
          key_owner: 2_383_326,
          nice: 0
        })
        |> IO.inspect()

      # TODO: Add update user task

      {:error, reason} ->
        Logger.debug(["Failed to verify user ", member.user_id, " on join due to ", reason])
    end
  end
end
