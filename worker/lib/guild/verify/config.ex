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

defmodule Tornium.Guild.Verify.Config do
  alias Tornium.Repo

  @type t :: %__MODULE__{
          verify_enabled: boolean(),
          auto_verify_enabled: boolean(),
          gateway_verify_enabled: boolean(),
          verify_template: String.t(),
          verified_roles: List,
          exclusion_roles: List,
          faction_verify: Map,
          verify_log_channel: integer(),
          verify_jail_channel: integer()
        }

  defstruct [
    :verify_enabled,
    :auto_verify_enabled,
    :gateway_verify_enabled,
    :verify_template,
    :verified_roles,
    :exclusion_roles,
    :faction_verify,
    :verify_log_channel,
    :verify_jail_channel
  ]

  @doc """
  Validate a server's configuration for the purposes of user verification

  ## Parameters
    - guild: Ecto struct of the server or the server ID

  ## Returns
    - Server verification configuration struct if valid
    - Error reason if not valid
  """
  @spec validate(guild :: Tornium.Schema.Server.t() | integer() | nil) ::
          Tornium.Guild.Verify.Config.t() | {:error, String}
  def validate(guild) when is_nil(guild) do
    {:error, "Invalid guild ID"}
  end

  def validate(guild_id) when is_integer(guild_id) do
    guild = Repo.get(Tornium.Schema.Server, guild_id)
    validate(guild)
  end

  def validate(%Tornium.Schema.Server{} = guild) when not guild.verify_enabled do
    {:error, "Verification is not enabled"}
  end

  def validate(%Tornium.Schema.Server{} = guild)
      when guild.verify_template == "" and Kernel.length(guild.verified_roles) == 0 and
             Kernel.length(guild.faction_verify) == 0 do
    {:error, "Verification is not configured"}
  end

  def validate(%Tornium.Schema.Server{} = guild) when Kernel.length(guild.admins) == 0 do
    {:error, "No server admins are signed into Tornium"}
  end

  def validate(%Tornium.Schema.Server{} = guild) do
    %Tornium.Guild.Verify.Config{
      verify_enabled: guild.verify_enabled,
      auto_verify_enabled: guild.auto_verify_enabled,
      gateway_verify_enabled: guild.gateway_verify_enabled,
      verify_template: guild.verify_template,
      verified_roles: guild.verified_roles,
      exclusion_roles: guild.exclusion_roles,
      faction_verify: guild.faction_verify,
      verify_log_channel: guild.verify_log_channel,
      verify_jail_channel: guild.verify_jail_channel
    }
  end
end
