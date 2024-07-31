defmodule Tornium.Discord.Consumer do
  require Logger
  use Nostrum.Consumer

  @spec handle_event({:GUILD_MEMBER_ADD, {guild_id :: integer(), new_member :: Nostrum.Struct.Guild.Member.t()}, Nostrum.Struct.WSState.t()}) :: any()
  def handle_event({:GUILD_MEMBER_ADD, {guild_id, new_member}, _ws_state}) do
    Tornium.Discord.Events.GuildMemberAdd.handle(guild_id, new_member)

    IO.inspect(new_member)
    Logger.info([Nostrum.Cache.UserCache.get(new_member.user_id).username, " [", new_member.user_id, "] has joined", guild_id])
  end
end
