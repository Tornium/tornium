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

defmodule Tornium.Guild.Verify.Message do
  @moduledoc """
  Generate Discord embeds for verification results.
  """

  @doc """
  Generate a Discord message describing the successful or failed verification of a member.

  NOTE: This is only for the verification of single members and not batch verification. See
  `Tornium.Workers.VerificationDiscordNotifications` for that.
  """
  @spec message(
          verification_result :: {:ok, Nostrum.Struct.Guild.Member.t()} | Tornium.Guild.Verify.verification_result(),
          member :: Nostrum.Struct.Guild.Member.t()
        ) :: Nostrum.Struct.Embed.t()
  def message({status_atom, data, _guild}, %Nostrum.Struct.Guild.Member{} = member) when status_atom in [:ok, :error] do
    message({status_atom, data}, member)
  end

  def message({:error, %Nostrum.Error.ApiError{} = error}, %Nostrum.Struct.Guild.Member{} = member) do
    %Nostrum.Struct.Embed{
      title: "Verification Failed - Discord Error",
      description:
        "<@#{member.user_id}> was not able to be verified as there was an error from Discord. #{Nostrum.Error.ApiError.message(error)}",
      color: Tornium.Discord.Constants.colors()[:error]
    }
  end

  def message(
        {:error, %Tornium.API.Error{code: code, message: message} = _error},
        %Nostrum.Struct.Guild.Member{} = member
      ) do
    %Nostrum.Struct.Embed{
      title: "Verification Failed - Torn Error",
      description:
        "<@#{member.user_id}> was not able to be verified as there was an error from the Torn API. [#{code}] #{message}",
      color: Tornium.Discord.Constants.colors()[:error]
    }
  end

  def message({:error, :unverified}, %Nostrum.Struct.Guild.Member{} = member) do
    %Nostrum.Struct.Embed{
      title: "Verification Failed",
      description:
        "<@#{member.user_id}> may not be verified on Torn. To verify on Torn, the user can link their Discord " <>
          "and Torn accounts through the [official Torn Discord server](https://www.torn.com/discord) or through a " <>
          "[direct OAuth link](https://discord.com/api/oauth2/authorize?client_id=439014098987122698&redirect_uri=https%3A%2F%2Fwww.torn.com%2Fdiscord.php&response_type=code&scope=identify)." <>
          "Once the user is verified, use `/verify frce:true` to verify the user.",
      color: Tornium.Discord.Constants.colors()[:error]
    }
  end

  def message({:error, :nochanges}, %Nostrum.Struct.Guild.Member{} = member) do
    %Nostrum.Struct.Embed{
      title: "Verification Already Complete",
      description: "The verification of <@#{member.user_id}> is already complete and nothing would change.",
      color: Tornium.Discord.Constants.colors()[:error]
    }
  end

  def message({:error, :exclusion_role}, %Nostrum.Struct.Guild.Member{} = _member) do
    %Nostrum.Struct.Embed{
      title: "Verification Already Complete",
      description:
        "The user has an exclusion role which prevents automatic verification. Contact a server admin to remove this exclusion role or to manually set roles.",
      color: Tornium.Discord.Constants.colors()[:error]
    }
  end

  def message({:error, :api_key}, %Nostrum.Struct.Guild.Member{} = _member) do
    %Nostrum.Struct.Embed{
      title: "No API keys",
      description: "No API keys of server admins were found to be used for this command.",
      color: Tornium.Discord.Constants.colors()[:error]
    }
  end

  def message({:error, {:config, error}}, %Nostrum.Struct.Guild.Member{} = member) do
    %Nostrum.Struct.Embed{
      title: "Invalid Verification Configuration",
      description: "The verification of <@#{member.user_id}> has failed as there is a(n) #{error}.",
      color: Tornium.Discord.Constants.colors()[:error]
    }
  end

  def message({:ok, %Nostrum.Struct.Guild.Member{} = updated_member}, %Nostrum.Struct.Guild.Member{} = original_member) do
    embed = %Nostrum.Struct.Embed{
      title: "Verification Complete",
      description: "The verification of <@#{original_member.user_id}> is successful.",
      color: Tornium.Discord.Constants.colors()[:good]
    }

    original_roles = MapSet.new(original_member.roles)
    updated_roles = MapSet.new(updated_member.roles)

    removed_roles = MapSet.difference(original_roles, updated_roles)
    added_roles = MapSet.difference(updated_roles, original_roles)

    embed =
      if updated_member.nick != original_member.nick do
        Nostrum.Struct.Embed.put_field(embed, "Nickname", "#{original_member.nick} -> #{updated_member.nick}")
      else
        embed
      end

    embed =
      if MapSet.size(removed_roles) > 0 do
        Nostrum.Struct.Embed.put_field(
          embed,
          "Removed Roles",
          Tornium.Discord.roles_to_string(MapSet.to_list(removed_roles))
        )
      else
        embed
      end

    embed =
      if MapSet.size(added_roles) > 0 do
        Nostrum.Struct.Embed.put_field(
          embed,
          "Added Roles",
          Tornium.Discord.roles_to_string(MapSet.to_list(added_roles))
        )
      else
        embed
      end

    embed
  end
end
