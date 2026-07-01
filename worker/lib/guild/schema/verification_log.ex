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

defmodule Tornium.Schema.VerificationLog do
  @moduledoc """
  Schema for verification logs when a user in a guild is updated.

  ## Errors
  When verification fails, the failure will be logged under one of the `errors()`:
    * `:unverified` - The member was not verified.
    * `:discord_permission` - Discord prevented the bot from changing the member's role/nickname.
    * `:no_api_key` - There was no API key to perform verification.
    * `:config` - Tornium was not configured to perform verification.
    * `:torn_api` - There was a Torn API error.
    * `:discord_api` - There was a Discord API error.

  The `:error_message` should only be set when the message would be distinct such as for the
  `:config` error. Otherwise, errors such as `:torn_api` can be identified from the `:error_code`
  and will have too many duplicate logs.
  """

  use Ecto.Schema
  alias Tornium.Repo

  @typedoc """
  Errors that can be logged during verification and are stored in the database.

  See the moduledoc for info on what each error is.
  """
  @type errors() :: :unverified | :discord_permission | :no_api_key | :config | :torn_api | :discord_api

  @type t :: %__MODULE__{
          guid: Ecto.UUID.t(),
          server_id: pos_integer(),
          server: Tornium.Schema.Server.t(),
          discord_id: pos_integer() | nil,
          user_id: pos_integer() | nil,
          user: Tornium.Schema.User.t() | nil,
          old_nickname: String.t() | nil,
          new_nickname: String.t() | nil,
          roles_added: [Tornium.Discord.role()],
          roles_removed: [Tornium.Discord.role()],
          error_type: errors() | nil,
          error_code: pos_integer() | nil,
          error_message: String.t() | nil,
          timestamp: DateTime.t()
        }

  @primary_key {:guid, Ecto.UUID, autogenerate: true}
  schema "verification_log" do
    belongs_to(:server, Tornium.Schema.Server, references: :sid)
    field(:discord_id, :integer)
    belongs_to(:user, Tornium.Schema.User, references: :tid)

    field(:old_nickname, :string)
    field(:new_nickname, :string)
    field(:roles_added, {:array, :integer})
    field(:roles_removed, {:array, :integer})

    field(:error_type, Ecto.Enum,
      values: [:unverified, :discord_permission, :no_api_key, :config, :torn_api, :discord_api]
    )

    field(:error_code, :integer)
    field(:error_message, :string)

    field(:timestamp, :utc_datetime)
  end

  @spec map(log :: t()) :: map()
  def map(
        %__MODULE__{
          server_id: server_id,
          discord_id: discord_id,
          user_id: user_id,
          old_nickname: old_nickname,
          new_nickname: new_nickname,
          roles_added: roles_added,
          roles_removed: roles_removed,
          error_type: error_type,
          error_code: error_code,
          error_message: error_message
        } = _log
      ) do
    %{
      guid: Ecto.UUID.generate(),
      server_id: server_id,
      discord_id: discord_id,
      user_id: user_id,
      old_nickname: old_nickname,
      new_nickname: new_nickname,
      roles_added: roles_added || [],
      roles_removed: roles_removed || [],
      error_type: dump_error_type(error_type),
      error_code: error_code,
      error_message: error_message,
      timestamp: DateTime.utc_now() |> DateTime.truncate(:second)
    }
  end

  @spec dump_error_type(error_type :: errors() | nil) :: String.t() | nil
  defp dump_error_type(error_type) when is_nil(error_type) do
    nil
  end

  defp dump_error_type(error_type) do
    # We need to convert the error type enum into a string ourselves as Repo.insert_all/3
    # is too low-level for these transformations.

    __MODULE__
    |> Ecto.Enum.mappings(:error_type)
    |> Keyword.get(error_type)
  end

  @doc """
  Insert multiple verification logs to the database.
  """
  @spec insert_all(logs :: [t()]) :: {non_neg_integer(), nil}
  def insert_all([] = _logs), do: {0, nil}

  def insert_all(logs) when is_list(logs) do
    Repo.insert_all(__MODULE__, Enum.map(logs, &map/1))
  end
end
