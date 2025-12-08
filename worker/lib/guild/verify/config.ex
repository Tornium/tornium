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

defmodule Tornium.Guild.Verify.Config do
  import Ecto.Query
  alias Tornium.Repo

  @type t :: %__MODULE__{
          guild_id: pos_integer(),
          verify_enabled: boolean(),
          auto_verify_enabled: boolean(),
          gateway_verify_enabled: boolean(),
          verify_template: String.t(),
          verified_roles: [Tornium.Discord.role()],
          unverified_roles: [Tornium.Discord.role()],
          exclusion_roles: [Tornium.Discord.role()],
          faction_verify: map(),
          verify_log_channel: integer(),
          verify_jail_channel: integer(),
          verify_elimination_config: [Tornium.Schema.ServerVerificationEliminationConfig.t()]
        }

  defstruct [
    :guild_id,
    :verify_enabled,
    :auto_verify_enabled,
    :gateway_verify_enabled,
    :verify_template,
    :verified_roles,
    :unverified_roles,
    :exclusion_roles,
    :faction_verify,
    :verify_log_channel,
    :verify_jail_channel,
    :verify_elimination_config
  ]

  @doc """
  Validate a server's configuration for the purposes of user verification

  If the elimination event is active, the elimination data will be loaded also if it already isn't loaded.

  ## Parameters
    - guild: Ecto struct of the server or the server ID

  ## Returns
    - Server verification configuration struct if valid
    - Error reason if not valid
  """
  @spec validate(guild :: Tornium.Schema.Server.t() | integer() | nil) :: t() | {:error, String.t()}
  def validate(guild) when is_nil(guild) do
    {:error, "Invalid guild ID"}
  end

  def validate(guild_id) when is_integer(guild_id) do
    Tornium.Schema.Server
    |> where([s], s.sid == ^guild_id)
    |> preload([s], verify_elimination_config: :team)
    |> first()
    |> Repo.one()
    |> validate()
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
    if Tornium.Elimination.active?() and not Ecto.assoc_loaded?(guild.verify_elimination_config) do
      # Since the elimination event is active and the elimination verification configuration is not loaded into
      # the struct, we should reload the struct from the database.
      validate(guild.sid)
    else
      %Tornium.Guild.Verify.Config{
        guild_id: guild.sid,
        verify_enabled: guild.verify_enabled,
        auto_verify_enabled: guild.auto_verify_enabled,
        gateway_verify_enabled: guild.gateway_verify_enabled,
        verify_template: guild.verify_template,
        verified_roles: guild.verified_roles,
        unverified_roles: guild.unverified_roles,
        exclusion_roles: guild.exclusion_roles,
        faction_verify: guild.faction_verify,
        verify_log_channel: guild.verify_log_channel,
        verify_jail_channel: guild.verify_jail_channel,
        verify_elimination_config: guild.verify_elimination_config
      }
    end
  end
end
