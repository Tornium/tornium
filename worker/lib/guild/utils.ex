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

defmodule Tornium.Guild do
  import Ecto.Query
  alias Tornium.Repo

  @spec get_admin_keys(guild :: integer() | Tornium.Schema.Server) :: List
  def get_admin_keys(guild) when is_integer(guild) do
    guild = Repo.get(Tornium.Schema.Server, guild)
    get_admin_keys(guild)
  end

  def get_admin_keys(guild) when is_nil(guild) or Kernel.length(guild.admins) == 0 do
    []
  end

  def get_admin_keys(guild) do
    Tornium.Schema.TornKey
    |> where([key], key.user_id in ^guild.admins and key.paused == false and key.default == true)
    |> Repo.all()
    |> Enum.map(fn key -> key.api_key end)
  end
end
