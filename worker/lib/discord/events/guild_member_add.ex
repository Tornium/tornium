defmodule Tornium.Discord.Events.GuildMemberAdd do
  require Logger

  @spec check_server_configuration(guild_id :: integer()) :: {:ok} | {:error}
  defp check_server_configuration(guild_id) do
    
  end

  @spec handle(guild_id :: integer(), new_member :: Nostrum.Struct.Guild.Member.t()) :: nil
  def handle(guild_id, new_member) do
    # Verify members on join if the server has that feature enabled
    case Nostrum.Cache.UserCache.get(new_member.user_id) do
      {:ok, user} ->
        check_server_configuration(guild_id)
        # |> tornget("user/{{ discord_id }}?selections=")
        # |> perform_verification()
      {:error, reason} ->
        Logger.debug(["Failed to get user ", new_member.user_id, " from the cache due to ", reason])
    end
  end
end
