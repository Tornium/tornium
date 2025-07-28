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

defmodule Tornium.Schema.Server do
  use Ecto.Schema
  alias Tornium.Repo

  @type t :: %__MODULE__{
          sid: non_neg_integer(),
          name: String.t(),
          admins: [non_neg_integer()],
          icon: String.t(),
          factions: [non_neg_integer()],
          verify_enabled: boolean(),
          auto_verify_enabled: boolean(),
          gateway_verify_enabled: boolean(),
          verify_template: String.t(),
          verified_roles: [Tornium.Discord.role()],
          exclusion_roles: [Tornium.Discord.role()],
          faction_verify: map(),
          verify_log_channel: integer(),
          verify_jail_channel: integer(),
          banking_config: map(),
          armory_enabled: boolean(),
          armory_config: map(),
          oc_config: map(),
          notifications_config: Tornium.Schema.ServerNotificationsConfig.t()
        }

  @primary_key {:sid, :integer, autogenerate: false}
  schema "server" do
    field(:name, :string)
    field(:admins, {:array, :integer})
    field(:icon, :string)

    field(:factions, {:array, :integer})

    field(:verify_enabled, :boolean)
    field(:auto_verify_enabled, :boolean)
    field(:gateway_verify_enabled, :boolean)
    field(:verify_template, :string)
    field(:verified_roles, {:array, :integer})
    field(:exclusion_roles, {:array, :integer})
    field(:faction_verify, :map)
    field(:verify_log_channel, :integer)
    field(:verify_jail_channel, :integer)

    field(:banking_config, :map)

    field(:armory_enabled, :boolean)
    field(:armory_config, :map)

    field(:oc_config, :map)

    has_one(:notifications_config, Tornium.Schema.ServerNotificationsConfig, foreign_key: :server_id, references: :sid)
  end

  @doc """
  Insert a new server by ID and name.
  """
  @spec new(guild_id :: non_neg_integer(), guild_name :: String.t(), opts :: Keyword.t()) :: t()
  def new(guild_id, guild_name, opts \\ []) when is_integer(guild_id) and is_binary(guild_name) do
    __MODULE__
    |> Ecto.Changeset.put_change(:sid, guild_id)
    |> Ecto.Changeset.put_change(:name, guild_name)
    |> Ecto.Changeset.change(opts)
    |> Repo.insert()
  end
end
