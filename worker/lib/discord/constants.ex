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

defmodule Tornium.Discord.Constants do
  @doc ~S"""
  Get all the pre-defined color constants.

  ## Examples
    iex> Tornium.Discord.Constants.colors()[:good]
    0x32CD32
  """
  @spec colors() :: %{any() => integer()}
  def colors() do
    %{
      good: 0x32CD32,
      error: 0xC83F49,
      warning: 0x755FBE,
      info: 0x7DF9FF
    }
  end
end
