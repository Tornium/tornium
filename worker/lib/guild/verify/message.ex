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

defmodule Tornium.Guild.Verify.Message do
  # TODO: Add docs
  @spec message(
          {:ok, Nostrum.Struct.Guild.Member.t()}
          | {:error,
             Nostrum.Error.ApiError
             | Tornium.API.Error
             | :unverified
             | :nochanges
             | :api_key
             | {:config, error :: String.t()}},
          member :: Nostrum.Struct.Guild.Member
        ) :: Nostrum.Struct.Embed
  def message({:error, :unverified}, %Nostrum.Struct.Guild.Member{} = member) do
    %Nostrum.Struct.Embed{
      title: "Verification Failed",
      description:
        "<@#{member.user_id}> may not be verified on Torn. To verify on Torn, the user can link their Discord " <>
          "and Torn accounts through the [official Torn Discord server](https://www.torn.com/discord) or through a " <>
          "[direct OAuth link](https://discordapp.com/api/oauth2/authorize?client_id=441210177971159041&redirect_uri=https%3A%2F%2Fwww.torn.com%2Fdiscord.php&response_type=code&scope=identify). " <>
          "Once the user is verified, use `/verify force:true` to verify the user.",
      color: 0xC83F49
    }
  end

  def message({:error, :nochanges}, %Nostrum.Struct.Guild.Member{} = member) do
    %Nostrum.Struct.Embed{
      title: "Verification Already Complete",
      description:
        "The verification of <@#{member.user_id}> is already complete and nothing would change. " <>
          "Execute `/verify force:true` if you believe something should have changed.",
      color: 0xC83F49
    }
  end

  def message({:error, :api_key}, %Nostrum.Struct.Guild.Member{} = _member) do
    %Nostrum.Struct.Embed{
      title: "No API keys",
      description: "No API keys of server admins were found to be used for this command.",
      color: 0xC83F49
    }
  end

  def message({:error, {:config, error}}, %Nostrum.Struct.Guild.Member{} = member) do
    %Nostrum.Struct.Embed{
      title: "Invalid Verification Configuration",
      description: "The verification of <@#{member.user_id}> has failed as there is a(n) #{error}.",
      color: 0xC83F49
    }
  end

  def message({:ok, %Nostrum.Struct.Guild.Member{} = updated_member}, %Nostrum.Struct.Guild.Member{} = original_member) do
    embed = %Nostrum.Struct.Embed{
      title: "Verification Complete",
      description: "The verification of <@#{original_member.user_id}> is successful.",
      color: 0x32CD32
    }

    original_roles = MapSet.new(original_member.roles)
    updated_roles = MapSet.new(updated_member.roles)

    removed_roles = MapSet.difference(original_roles, updated_roles)
    added_roles = MapSet.difference(updated_roles, original_roles)

    if updated_member.nick != original_member.nick do
      Nostrum.Struct.Embed.put_field(embed, "Nickname", "#{original_member.nick} -> #{updated_member.nick}")
    end

    if MapSet.size(removed_roles) > 0 do
      Nostrum.Struct.Embed.put_field(
        embed,
        "Removed Roles",
        Tornium.Utils.roles_to_string(MapSet.to_list(removed_roles))
      )
    end

    if MapSet.size(added_roles) > 0 do
      Nostrum.Struct.Embed.put_field(embed, "Added Roles", Tornium.Utils.roles_to_string(MapSet.to_list(added_roles)))
    end

    embed
  end
end
