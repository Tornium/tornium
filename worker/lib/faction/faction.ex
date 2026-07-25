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

defmodule Tornium.Faction do
  @moduledoc """
  Faction-related utilities.
  """

  import Ecto.Query
  alias Tornium.Repo

  @doc """
  Get all AA keys for the faction.
  """
  @spec get_keys(faction_id :: pos_integer()) :: [Tornium.Schema.TornKey.t()]
  def get_keys(faction_id) when is_integer(faction_id) do
    Tornium.Schema.TornKey
    |> where([k], k.default == true and k.disabled == false and k.paused == false)
    |> join(:inner, [k], u in assoc(k, :user), on: u.tid == k.user_id)
    |> where([k, u], u.faction_id == ^faction_id)
    |> where([k, u], u.faction_aa == true)
    |> Repo.all()
  end

  @doc """
  Get a random AA key for the faction.
  """
  @spec get_key(faction_id :: pos_integer()) :: Tornium.Schema.TornKey.t() | nil
  def get_key(faction_id) when is_integer(faction_id) do
    Tornium.Schema.TornKey
    |> where([k], k.default == true and k.disabled == false and k.paused == false)
    |> join(:inner, [k], u in assoc(k, :user), on: u.tid == k.user_id)
    |> where([k, u], u.faction_id == ^faction_id)
    |> where([k, u], u.faction_aa == true)
    |> order_by(fragment("RANDOM()"))
    |> first()
    |> Repo.one()
  end
end
