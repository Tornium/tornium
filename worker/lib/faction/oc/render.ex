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
  @moduledoc ~S"""
  Functions to render the embeds and components of OC-related notifications.
  """

  import Ecto.Query
  alias Tornium.Repo

  # TODO: Add color to the embeds

  # TODO: Document function
  @spec render_all(check_state :: Tornium.Faction.OC.Check.Struct.t(), faction_id :: integer()) :: [
          Nostrum.Struct.Message.t()
        ]
  def render_all(%Tornium.Faction.OC.Check.Struct{} = check_state, faction_id) when is_integer(faction_id) do
    faction =
      Tornium.Schema.Faction
      |> join(:inner, [f], s in assoc(f, :guild_id), on: f.guild_id == s.sid)
      |> where([f, s], f.tid == ^faction_id)
      |> preload([f, s], guild: s)
      |> Repo.one()

    # TODO: Select necessary fields

    config =
      Tornium.Schema.ServerOCConfig
      |> where([c], c.server_id == ^faction.guild_id and c.faction_id == ^faction_id)
      |> Repo.one()

    if faction != nil and config != nil and Enum.member?(faction.guild.factions, faction_id) do
      render_all(check_state, faction_id, config)
    else
      []
    end
  end

  @spec render_all(
          check_state :: Tornium.Faction.OC.Check.Struct.t(),
          faction_id :: integer(),
          config :: Tornium.Schema.ServerOCConfig.t()
        ) :: [
          Nostrum.Struct.Message.t()
        ]
  def render_all(
        %Tornium.Faction.OC.Check.Struct{} = check_state,
        _faction_id,
        %Tornium.Schema.ServerOCConfig{} = config
      ) do
    []
    |> render_feature(:missing_tools, check_state.missing_tools, config)
    |> render_feature(:delayers, check_state.delayers, config)
  end

  # TODO: Test function
  # TODO: Document function
  @spec render_feature(
          messages :: [Nostrum.Struct.Message.t()],
          state_element :: Tornium.Faction.OC.Check.Struct.keys(),
          slots :: [Tornium.Schema.OrganizedCrimeSlot.t()],
          config :: Tornium.Schema.ServerOCConfig.t()
        ) :: [Nostrum.Struct.Message.t()]
  def render_feature(
        messages,
        :missing_tools,
        [
          %Tornium.Schema.OrganizedCrimeSlot{
            oc: %Tornium.Schema.OrganizedCrime{} = crime,
            user: %Tornium.Schema.User{} = user,
            crime_position: position,
            item_required: %Tornium.Schema.Item{} = item
          } = slot
          | remaining_slots
        ],
        %Tornium.Schema.ServerOCConfig{tool_channel: tool_channel, tool_roles: tool_roles, tool_crimes: tool_crimes} =
          config
      )
      when is_list(messages) do
    # TODO: Restructure this code
    # Maybe split the message struct creation into a separate function

    messages =
      if render_crime?(slot, tool_crimes) do
        [
          %Nostrum.Struct.Message{
            channel_id: tool_channel,
            content: Tornium.Utils.roles_to_string(tool_roles),
            embeds: [
              %Nostrum.Struct.Embed{
                title: "OC Missing Tool",
                description:
                  "Member #{user.name} [#{user.tid}] in position #{position} is missing #{item.name} [#{item.tid}] for an #{crime.oc_name} OC.",
                footer: %Nostrum.Struct.Embed.Footer{text: "OC ID: #{crime.oc_id}"}
              }
            ],
            components: [
              %Nostrum.Struct.Component{
                type: 1,
                components: [
                  %Nostrum.Struct.Component{
                    type: 2,
                    style: 5,
                    label: "#{user.name} [#{user.tid}]",
                    url: "https://www.torn.com/profiles.php?XID=#{user.tid}"
                  },
                  %Nostrum.Struct.Component{
                    type: 2,
                    style: 5,
                    label: "Organized Crime",
                    url: "https://www.torn.com/factions.php?step=your&type=1#/tab=crimes&crimeId=#{crime.oc_id}"
                  }
                ]
              }
            ]
          }
          | messages
        ]
      else
        messages
      end

    render_all(messages, :missing_tools, remaining_slots, config)
  end

  def render_feature(
        messages,
        :delayers,
        [
          %Tornium.Schema.OrganizedCrimeSlot{
            oc: %Tornium.Schema.OrganizedCrime{} = crime,
            user: %Tornium.Schema.User{} = user,
            crime_position: position,
            delayer: true,
            delayed_reason: delayed_reason
          } = slot
          | remaining_slots
        ],
        %Tornium.Schema.ServerOCConfig{delayed_channel: delayed_channel, delayed_roles: delayed_roles, delayed_crimes: delayed_crimes} =
          config
      )
      when is_list(messages) do
    # TODO: Restructure this code
    # Maybe split the message struct creation into a separate function

    messages =
      if render_crime?(slot, delayed_crimes) do
        [
          %Nostrum.Struct.Message{
            channel_id: delayed_channel,
            content: Tornium.Utils.roles_to_string(delayed_roles),
            embeds: [
              %Nostrum.Struct.Embed{
                title: "OC Delayed",
                description:
                  "Member #{user.name} [#{user.tid}] in position #{position} is delaying an #{crime.oc_name} OC.",
                fields: [
                  %Nostrum.Struct.Embed.Field{name: "Reason", value: delayed_reason}
                ],
                footer: %Nostrum.Struct.Embed.Footer{text: "OC ID: #{crime.oc_id}"}
              }
            ],
            components: [
              %Nostrum.Struct.Component{
                type: 1,
                components: [
                  %Nostrum.Struct.Component{
                    type: 2,
                    style: 5,
                    label: "#{user.name} [#{user.tid}]",
                    url: "https://www.torn.com/profiles.php?XID=#{user.tid}"
                  },
                  %Nostrum.Struct.Component{
                    type: 2,
                    style: 5,
                    label: "Organized Crime",
                    url: "https://www.torn.com/factions.php?step=your&type=1#/tab=crimes&crimeId=#{crime.oc_id}"
                  }
                ]
              }
            ]
          }
          | messages
        ]
      else
        messages
      end

    render_all(messages, :delayers, remaining_slots, config)
  end

  def render_all(messages, _state_element, [] = _slots, %Tornium.Schema.ServerOCConfig{} = _config) do
    messages
  end

  @doc ~S"""
  Truthy value for whether an OC should be rendered for a feature depending on the configuration for that crime. If the feature is not configured to work for specific crimes, then it will work for all crimes. Otherwise the filter works as a whitelist.

  ## Examples
    iex> Tornium.Faction.OC.Render.render_crime?(%Tornium.Schema.OrganizedCrimeSlot{oc: %Tornium.Schema.OrganizedCrime{oc_name: "Honey Trap"}}, [])
    true
    iex> Tornium.Faction.OC.Render.render_crime?(%Tornium.Schema.OrganizedCrimeSlot{oc: %Tornium.Schema.OrganizedCrime{oc_name: "Honey Trap"}}, ["Stage Fright"])
    false
    iex> Tornium.Faction.OC.Render.render_crime?(%Tornium.Schema.OrganizedCrimeSlot{oc: %Tornium.Schema.OrganizedCrime{oc_name: "Honey Trap"}}, ["Stage Fright", "Honey Trap"])
    true
  """
  @spec render_crime?(slot :: Tornium.Schema.OrganizedCrimeSlot.t(), crime_filter :: [String.t()]) :: boolean()
  def render_crime?(%Tornium.Schema.OrganizedCrimeSlot{} = _slot, [] = _crime_filter) do
    true
  end

  def render_crime?(
        %Tornium.Schema.OrganizedCrimeSlot{oc: %Tornium.Schema.OrganizedCrime{oc_name: oc_name}} = _slot,
        crime_filter
      ) do
    Enum.member?(crime_filter, oc_name)
  end
end
