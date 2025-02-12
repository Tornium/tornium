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

defmodule Tornium.Faction.OC.Render do
  import Ecto.Query
  alias Tornium.Repo

  @spec render_all(check_state :: Tornium.Faction.OC.Check.Struct.t(), faction_id :: integer()) :: [
          Nostrum.Struct.Message.t()
        ]
  def render_all(%Tornium.Faction.OC.Check.Struct{} = check_state, faction_id) when is_integer(faction_id) do
    guild =
      Tornium.Schema.Faction
      |> join(:inner, [f], s in assoc(f, :guild_id), on: f.guild_id == s.sid)
      |> where([f, s], f.tid == ^faction_id)
      |> preload([f, s], guild: s)
      |> Repo.one()

    render_all(check_state, faction_id, guild)
  end

  @spec render_all(
          check_state :: Tornium.Faction.OC.Check.Struct.t(),
          faction_id :: integer(),
          guild :: Tornium.Schema.Server.t() | nil
        ) :: [
          Nostrum.Struct.Message.t()
        ]
  def render_all(%Tornium.Faction.OC.Check.Struct{} = _check_state, _faction_id, guild) when is_nil(guild) do
    []
  end

  def render_all(%Tornium.Faction.OC.Check.Struct{} = check_state, _faction_id, %Tornium.Schema.Server{} = guild) do
    []
    |> render_all(:missing_tools, check_state.missing_tools, guild)
  end

  @spec render_all(
          messages :: [Nostrum.Struct.Message.t()],
          state_element :: Tornium.Faction.OC.Check.Struct.keys(),
          slots :: [Tornium.Schema.OrganizedCrimeSlot.t()],
          guild :: Tornium.Schema.Server.t()
        ) :: [Nostrum.Struct.Message.t()]
  def render_all(
        messages,
        :missing_tools,
        [%Tornium.Schema.OrganizedCrimeSlot{} = _slot | remaining_slots],
        %Tornium.Schema.Server{} = guild
      )
      when is_list(messages) do
    %Nostrum.Struct.Message{
      embeds: [
        %Nostrum.Struct.Embed{
          title: "foo"
        }
      ]
    }

    render_all(messages, :missing_tools, remaining_slots, guild)
  end

  def render_all(messages, _state_element, [] = _slots, %Tornium.Schema.Server{} = _guild) do
    messages
  end
end
