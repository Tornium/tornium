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

defmodule Tornium.Faction.News do
  @moduledoc """
  Parser for faction news data from `faction/news`.
  """

  @doc """
  Parse a faction news for a specific category.
  """
  @spec parse(
          category :: Torngen.Client.Schema.FactionNewsCategory.t(),
          news_data :: [Torngen.Client.Schema.FactionNews.t()]
        ) :: [struct()]
  def parse("armoryAction", [%Torngen.Client.Schema.FactionNews{} | _] = news_data) do
    now = DateTime.utc_now()

    news_data
    |> Enum.reject(fn %Torngen.Client.Schema.FactionNews{timestamp: news_timestamp} ->
      # We want to reject extremely old faction news as the format changed at some point
      # and we don't need to support this.
      seconds_diff =
        news_timestamp
        |> DateTime.from_unix!()
        |> DateTime.diff(now)
        |> abs()

      seconds_diff / 3600 / 24 / 365 > 2
    end)
    |> Enum.map(&Tornium.Faction.News.ArmoryAction.parse/1)
    |> Enum.reject(&is_nil/1)
  end

  def parse(_category, [] = _news_data) do
    []
  end

  @doc """
  Parse a faction news struct from Torn for a specific category.
  """
  @callback parse(news :: Torngen.Client.Schema.FactionNews.t()) :: struct() | nil
end
