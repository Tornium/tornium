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

defmodule Tornium.User.Key do
  import Ecto.Query

  alias Tornium.Repo

  @spec get_by_user(user :: Tornium.Schema.User.t()) :: Tornium.Schema.TornKey.t() | nil
  def get_by_user(%Tornium.Schema.User{} = user) do
    pid = Process.whereis(Tornium.User.KeyStore)
    get_by_user(user, pid)
  end

  @spec get_by_user(user :: Tornium.Schema.User.t(), pid :: pid()) :: Tornium.Schema.TornKey.t() | nil
  def get_by_user(%Tornium.Schema.User{} = user, pid) when not is_nil(pid) do
    case Tornium.User.KeyStore.get(pid, user.tid) do
      nil ->
        where = [user_id: user.tid, paused: false, disabled: false, default: true]
        query = from(Tornium.Schema.TornKey, where: ^where)
        torn_key = Repo.one(query)
        Tornium.User.KeyStore.put(pid, user.tid, torn_key)
        torn_key

      torn_key ->
        torn_key
    end
  end
end
