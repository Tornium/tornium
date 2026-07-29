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
  @moduledoc """
  Verification configuration for a faction in a Discord server.
  """

  alias Tornium.Repo

  @typedoc """
  Verification configuration for a specific faction.

  The values of the map are only the following with the following types:
  `"roles"` - `[Tornium.Discord.role()]`
  `"positions"` - `%{Ecto.UUID.t() => [Tornium.Discord.role()]}`
  `"enabled"` - `boolean()`
  where the LHS is the key and the RHS is the type of the value.
  """
  @type faction_verify_config() :: %{
          String.t() => [Tornium.Discord.role()] | %{Ecto.UUID.t() => [Tornium.Discord.role()]} | boolean()
        }

  @type t :: %__MODULE__{
          verify_enabled: boolean(),
          auto_verify_enabled: boolean(),
          gateway_verify_enabled: boolean(),
          verify_template: String.t(),
          verified_roles: [Tornium.Discord.role()],
          unverified_roles: [Tornium.Discord.role()],
          exclusion_roles: [Tornium.Discord.role()],
          faction_verify: %{String.t() => faction_verify_config()},
          verify_log_channel: integer(),
          verify_jail_channel: integer()
        }

  defstruct [
    :verify_enabled,
    :auto_verify_enabled,
    :gateway_verify_enabled,
    :verify_template,
    :verified_roles,
    :unverified_roles,
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
  @spec validate(guild :: Tornium.Schema.Server.t() | integer() | nil) :: t() | {:error, String.t()}
  def validate(guild) when is_nil(guild) do
    {:error, "Invalid guild ID"}
  end

  def validate(guild_id) when is_integer(guild_id) do
    Tornium.Schema.Server
    |> Repo.get(guild_id)
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
    %Tornium.Guild.Verify.Config{
      verify_enabled: guild.verify_enabled,
      auto_verify_enabled: guild.auto_verify_enabled,
      gateway_verify_enabled: guild.gateway_verify_enabled,
      verify_template: guild.verify_template,
      verified_roles: guild.verified_roles,
      unverified_roles: guild.unverified_roles,
      exclusion_roles: guild.exclusion_roles,
      faction_verify: guild.faction_verify |> normalize_faction_verify_roles(),
      verify_log_channel: guild.verify_log_channel,
      verify_jail_channel: guild.verify_jail_channel
    }
  end

  defp normalize_faction_verify_roles(faction_verify) when is_map(faction_verify) do
    # As the database is storing the faction verify incorrectly with strings for the role
    # IDs for faction positions' verification roles, we need to convert them to integers.

    Map.new(faction_verify, fn {faction_id, faction_config} ->
      updated_positions =
        faction_config
        |> Map.get("positions", %{})
        |> Enum.map(fn {position_id, roles} ->
          {position_id, Enum.map(roles, &string_to_integer/1)}
        end)
        |> Map.new()

      updated_faction_roles =
        faction_config
        |> Map.get("roles")
        |> List.wrap()
        |> Enum.map(&string_to_integer/1)

      updated_config =
        faction_config
        |> Map.put("positions", updated_positions)
        |> Map.put("roles", updated_faction_roles)

      {faction_id, updated_config}
    end)
  end

  # The Tornium.Utils.string_to_integer/1 returns nil if the value is not a string, so
  # that can not be used for this.
  @spec string_to_integer(value :: String.t() | integer()) :: integer()
  defp string_to_integer(value) when is_binary(value) do
    String.to_integer(value)
  end

  defp string_to_integer(value) when is_integer(value) do
    value
  end
end
