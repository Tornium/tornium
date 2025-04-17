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
  @moduledoc """
  Functions to render the embeds and components of OC-related notifications.
  """

  @doc """
  Render embeds for each failed check listed for each feature in `Tornium.Faction.OC.Check.Struct`.
  """
  @spec render_all(
          check_state :: Tornium.Faction.OC.Check.Struct.t(),
          config :: Tornium.Schema.ServerOCConfig.t()
        ) :: [
          Nostrum.Struct.Message.t()
        ]
  def render_all(
        %Tornium.Faction.OC.Check.Struct{} = check_state,
        %Tornium.Schema.ServerOCConfig{} = config
      ) do
    []
    |> render_feature(:missing_tools, check_state.missing_tools, config)
    |> render_feature(:delayers, check_state.delayers, config)
    |> render_feature(:extra_range, check_state.extra_range, config)
  end

  def render_all(
        %Tornium.Faction.OC.Check.Struct{} = check_state,
        config
      )
      when is_nil(config) do
    []
  end

  # TODO: Write test for this series of functions
  @doc """
  Render embeds for each failed check for a specific feature in `Tornium.Faction.OC.Check.Struct`.
  """
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
        %Tornium.Schema.ServerOCConfig{
          # enabled: true,
          tool_channel: tool_channel,
          tool_roles: tool_roles,
          tool_crimes: tool_crimes
        } =
          config
      )
      when is_list(messages) and not is_nil(tool_channel) do
    # TODO: Restructure this code
    # Maybe split the message struct creation into a separate function

    # FIXME: Re-enable the `enabled` check once the UI for that is created

    # TODO: Add commas to market value of item
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
                  "#{item.name} [#{item.tid}] is required for #{user.faction.name} member #{user.name} [#{user.tid}] (#{position}) in the #{crime.oc_name} (T#{crime.oc_difficulty}) OC.",
                color: Tornium.Discord.Constants.colors()[:error],
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
              },
              %Nostrum.Struct.Component{
                type: 1,
                components: [
                  %Nostrum.Struct.Component{
                    type: 2,
                    style: 5,
                    label: "Purchase #{item.name}",
                    url:
                      "https://www.torn.com/page.php?sid=ItemMarket#/market/view=search&itemID=#{item.tid}&itemName=Tornium"
                  },
                  %Nostrum.Struct.Component{
                    type: 2,
                    style: 2,
                    label: "MV: $#{item.market_value}",
                    disabled: true,
                    custom_id: "oc:missing-tool:#{slot.oc_id}"
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

    render_feature(messages, :missing_tools, remaining_slots, config)
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
        %Tornium.Schema.ServerOCConfig{
          # enabled: true,
          delayed_channel: delayed_channel,
          delayed_roles: delayed_roles,
          delayed_crimes: delayed_crimes
        } =
          config
      )
      when is_list(messages) and not is_nil(delayed_channel) do
    # TODO: Restructure this code
    # Maybe split the message struct creation into a separate function

    # FIXME: Re-enable the `enabled` check once the UI for that is created

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
                  "#{String.capitalize(user.faction.name)} member #{user.name} [#{user.tid}] (#{position}) is delaying an #{crime.oc_name} (T#{crime.oc_difficulty}) OC ... is #{String.downcase(delayed_reason)}.",
                color: Tornium.Discord.Constants.colors()[:error],
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

    render_feature(messages, :delayers, remaining_slots, config)
  end

  def render_feature(
        messages,
        :extra_range,
        [
          %Tornium.Schema.OrganizedCrimeSlot{
            oc: %Tornium.Schema.OrganizedCrime{} = crime,
            user: %Tornium.Schema.User{} = user,
            user_success_chance: chance
          } = _slot
          | remaining_slots
        ],
        %Tornium.Schema.ServerOCConfig{
          # enabled: true,
          extra_range_channel: extra_range_channel,
          extra_range_roles: extra_range_roles
        } =
          config
      )
      when is_list(messages) and not is_nil(extra_range_channel) do
    # TODO: Restructure this code
    # Maybe split the message struct creation into a separate function

    # FIXME: Re-enable the `enabled` check once the UI for that is created

    {expected_minimum, expected_maximum} = Tornium.Schema.ServerOCConfig.chance_range(config, crime)

    new_message =
      %Nostrum.Struct.Message{
        channel_id: extra_range_channel,
        content: Tornium.Utils.roles_to_string(extra_range_roles),
        embeds: [
          %Nostrum.Struct.Embed{
            title: "OC CPR Extra-Range",
            description:
              "#{String.capitalize(crime.faction.name)} member #{user.name} [#{user.tid}] in the #{crime.oc_name} (T#{crime.oc_difficulty}) OC has a CPR of #{chance}%. The expected CPR bounds are #{expected_minimum}% to #{expected_maximum}%.",
            color: Tornium.Discord.Constants.colors()[:warning],
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

    render_feature([new_message | messages], :extra_range, remaining_slots, config)
  end

  def render_feature(messages, _state_element, _slots, %Tornium.Schema.ServerOCConfig{} = _config) do
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
