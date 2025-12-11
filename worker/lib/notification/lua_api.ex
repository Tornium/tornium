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

defmodule Tornium.Notification.Lua.API do
  @moduledoc """
  Module containing API functions injected into the Lua VM used for notifications.
  """

  use Lua.API, scope: "tornium"

  @doc """
  Get a user's Discord ID by their Torn ID.
  """
  deflua get_discord_id(user_id) do
    user_id
    |> trunc()
    |> Tornium.User.DiscordStore.get()
  end
end
