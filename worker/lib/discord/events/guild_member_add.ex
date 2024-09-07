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

defmodule Tornium.Discord.Events.GuildMemberAdd do
  require Logger

  @spec handle(guild_id :: integer(), new_member :: Nostrum.Struct.Guild.Member.t()) :: nil
  def handle(guild_id, new_member) do
    # Verify members on join if the server has that feature enabled
    case Nostrum.Cache.UserCache.get(new_member.user_id) do
      {:ok, user} ->
        handle_verification(guild_id, user, new_member)

      {:error, reason} ->
        Logger.debug([
          "Failed to get user ",
          new_member.user_id,
          " for verification on join from the cache due to ",
          reason
        ])
    end
  end

  @spec handle_verification(
          guild_id :: integer(),
          user :: Nostrum.Struct.User.t(),
          member :: Nostrum.Struct.Guild.Member.t()
        ) :: nil
  defp handle_verification(guild_id, _user, member) do
    guild_config = Tornium.Guild.Config.validate(guild_id)

    case Tornium.Guild.Config.validate(guild_id) do
      :ok ->
        Tornex.Scheduler.Bucket.enqueue(%Tornex.Query{
          resource: "user",
          resource_id: member.user_id,
          selections: "",
          key: "",
          key_owner: 2_383_326,
          nice: 0
        })
        |> IO.inspect()
        |> validate_api_response()

      {:error, reason} ->
        Logger.debug(["Failed to verify user ", member.user_id, " on join due to ", reason])
    end
  end

  @spec validate_api_response(api_response :: map()) :: nil
  defp validate_api_response(api_response) do
  end
end
