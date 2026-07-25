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
    case user_id do
      _ when is_integer(user_id) ->
        Tornium.User.DiscordStore.get(user_id)

      _ when is_number(user_id) or is_float(user_id) ->
        user_id
        |> trunc()
        |> get_discord_id()

      _ when is_binary(user_id) ->
        {parsed_user_id, _binary_rest} = Float.parse(user_id)

        parsed_user_id
        |> trunc()
        |> get_discord_id()
    end
  end

  @doc """
  Convert a string of "true" or "false" into their boolean equivalents. If it does not match, it
  will fallback to `nil`.
  """
  deflua to_boolean(value) when is_binary(value) do
    value = String.downcase(value)

    case value do
      _ when value in ["true", "1"] ->
        true

      _ when value in ["false", "0"] ->
        false

      _ ->
        nil
    end
  end

  deflua to_boolean(value) when value in [0, 1] do
    value
    |> Integer.to_string()
    |> to_boolean()
  end

  deflua to_boolean(_value) do
    nil
  end
end
