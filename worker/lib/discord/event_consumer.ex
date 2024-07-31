defmodule Tornium.Discord.Consumer do
  use Nostrum.Consumer

  @spec handle_event(Nostrum.Consumer.guild_member_add()) :: nil
  def handle_event({:GUILD_MEMBER_ADD, guild_id, new_member, _ws_state}) do
    # Verify members upon guild join
  end
end
