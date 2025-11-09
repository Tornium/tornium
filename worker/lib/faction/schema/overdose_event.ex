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

defmodule Tornium.Schema.OverdoseEvent do
  @moduledoc """
  Schema for overdose events within a faction.
  """

  use Ecto.Schema
  import Ecto.Query
  alias Tornium.Repo

  @type t :: %__MODULE__{
          guid: Ecto.UUID.t(),
          faction_id: integer(),
          faction: Tornium.Schema.Faction.t(),
          user_id: integer(),
          user: Tornium.Schema.User.t(),
          created_at: DateTime.t(),
          notified_at: DateTime.t() | nil,
          drug: Tornium.Schema.Item.t() | nil
        }

  @primary_key {:guid, Ecto.UUID, autogenerate: true}
  schema "overdose_event" do
    belongs_to(:faction, Tornium.Schema.Faction, references: :tid)
    belongs_to(:user, Tornium.Schema.User, references: :tid)

    field(:created_at, :utc_datetime)
    field(:notified_at, :utc_datetime)

    belongs_to(:drug, Tornium.Schema.Item, references: :tid)
  end

  @doc """
  Mark all overdose events as notified at the current datetime.
  """
  def notify_all(events) when is_list(events) do
    event_guids = Enum.map(events, fn %__MODULE__{guid: guid} -> guid end)

    __MODULE__
    |> where([e], e.guid in ^event_guids)
    |> update([e], set: [notified_at: ^DateTime.utc_now()])
    |> Repo.update_all([])
  end

  @doc """
  Mark the overdose event as notified at the current datetime.
  """
  def notify(%__MODULE__{guid: guid}) do
    __MODULE__
    |> where([e], e.guid == ^guid)
    |> update([e], set: [notified_at: ^DateTime.utc_now()])
    |> Repo.update_all([])
  end
end
