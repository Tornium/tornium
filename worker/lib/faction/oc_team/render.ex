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

defmodule Tornium.Faction.OC.Team.Render do
  @moduledoc """
  Functions to render the embeds and components of OC team-related notifications.
  """

  import Ecto.Query
  alias Tornium.Repo

  @doc """
  Render embeds for each triggered check listed for each feature in `Tornium.Faction.OC.Team.Check.Struct`.
  """
  @spec render_all(
          check_state :: Tornium.Faction.OC.Team.Check.Struct.t(),
          config :: Tornium.Schema.ServerOCConfig.t()
        ) :: [Nostrum.Struct.Message.t()]
  def render_all(
        %Tornium.Faction.OC.Team.Check.Struct{} = check_state,
        %Tornium.Schema.ServerOCConfig{} = config
      ) do
    []
    |> render_feature(:team_spawn_required, check_state.team_spawn_required, config)
    |> render_feature(:team_member_join_required, check_state.team_member_join_required, config)
    |> render_feature(:team_member_incorrect_crime, check_state.team_member_incorrect_crime, config)
    |> render_feature(:team_incorrect_member, check_state.team_incorrect_member, config)
    |> render_feature(:team_member_incorrect_slot, check_state.team_member_incorrect_slot, config)
    |> render_feature(:assigned_team, check_state.assigned_team, config)
  end

  def render_all(
        %Tornium.Faction.OC.Team.Check.Struct{} = _check_state,
        config
      )
      when is_nil(config) do
    []
  end

  # The below apply to all render_feature/4 functions
  # TODO: Add link to Tornium's OC page and autoload the OC there
  # TODO: Add link to Tornium's OC page and autoload the OC team there
  # FIXME: Re-enable the `enabled` check once the UI for that is created

  # TODO: Write test for this series of functions
  @doc """
  Render embeds for each failed check for a specific feature in `Tornium.Faction.OC.Team.Check.Struct`.
  """
  @spec render_feature(
          messages :: [Nostrum.Struct.Message.t()],
          state_element :: Tornium.Faction.OC.Team.Check.Struct.keys(),
          slots :: [Tornium.Schema.OrganizedCrimeTeam.t()],
          config :: Tornium.Schema.ServerOCConfig.t()
        ) :: [Nostrum.Struct.Message.t()]
  def render_feature(
        messages,
        :team_spawn_required,
        [
          %Tornium.Schema.OrganizedCrimeTeam{
            guid: team_guid,
            name: team_name,
            faction: %Tornium.Schema.Faction{name: faction_name},
            oc_name: oc_name
          } = _slot
          | remaining_slots
        ],
        %Tornium.Schema.ServerOCConfig{
          team_spawn_required_channel: team_spawn_required_channel,
          team_spawn_required_roles: team_spawn_required_roles
          # enabled: true,
        } = config
      )
      when is_list(messages) and not is_nil(team_spawn_required_channel) do
    messages =
      [
        %Nostrum.Struct.Message{
          channel_id: team_spawn_required_channel,
          content: Tornium.Utils.roles_to_string(team_spawn_required_roles),
          embeds: [
            %Nostrum.Struct.Embed{
              title: "OC Spawn Required",
              description: "An #{oc_name} OC needs to be spawned in #{faction_name} for the #{team_name} OC team.",
              color: Tornium.Discord.Constants.colors()[:error],
              footer: %Nostrum.Struct.Embed.Footer{text: "Team ID: #{team_guid}"}
            }
          ],
          components: [
            %Nostrum.Struct.Component{
              type: 1,
              components: [
                %Nostrum.Struct.Component{
                  type: 2,
                  style: 5,
                  label: "Organized Crimes",
                  url: "https://www.torn.com/factions.php?step=your&type=1#faction-crimes"
                }
              ]
            }
          ]
        }
        | messages
      ]

    render_feature(messages, :team_spawn_required, remaining_slots, config)
  end

  def render_feature(
        messages,
        :team_member_join_required,
        [
          {
            %Tornium.Schema.OrganizedCrimeTeamMember{
              slot_type: oc_slot_type,
              slot_index: oc_slot_index,
              team_id: team_guid
            },
            %Tornium.Schema.OrganizedCrime{oc_name: oc_name, oc_id: oc_id}
          }
          | remaining_joins_required
        ],
        %Tornium.Schema.ServerOCConfig{
          team_member_join_required_channel: team_member_join_required_channel,
          team_member_join_required_roles: team_member_join_required_roles
          # enabled: true
        } = config
      )
      when is_list(messages) and not is_nil(team_member_join_required_channel) do
    messages = [
      %Nostrum.Struct.Message{
        channel_id: team_member_join_required_channel,
        # TODO: Add mention and assigns for user that needs to join
        content: Tornium.Utils.roles_to_string(team_member_join_required_roles),
        embeds: [
          %Nostrum.Struct.Embed{
            title: "OC Join Required",
            description:
              "<@> needs to join the #{oc_slot_type} ##{oc_slot_index} #{oc_name} OC assigned to their OC team.",
            color: Tornium.Discord.Constants.colors()[:warning],
            footer: %Nostrum.Struct.Embed.Footer{text: "Team ID: #{team_guid} | OC ID: #{oc_id}"}
          }
        ],
        components: [
          %Nostrum.Struct.Component{
            type: 1,
            components: [
              %Nostrum.Struct.Component{
                type: 2,
                style: 5,
                label: "Assigned OC",
                url: "https://www.torn.com/factions.php?step=your&type=1#/tab=crimes&crimeId=#{oc_id}"
              }
            ]
          }
        ]
      }
      | messages
    ]

    render_feature(messages, :team_member_join_required, remaining_joins_required, config)
  end

  def render_feature(
        messages,
        :team_member_incorrect_crime,
        [
          {
            %Tornium.Schema.OrganizedCrimeTeamMember{
              slot_type: oc_slot_type,
              slot_index: oc_slot_index,
              user: %Tornium.Schema.User{name: member_name, tid: member_id},
              team_id: team_guid
            },
            %Tornium.Schema.OrganizedCrime{oc_name: incorrect_oc_name, oc_id: incorrect_oc_id} = _incorrect_crime,
            %Tornium.Schema.OrganizedCrime{oc_name: assigned_oc_name, oc_id: assigned_oc_id} = _assigned_crime
          }
          | remaining_incorrect_crimes
        ],
        %Tornium.Schema.ServerOCConfig{
          team_member_incorrect_crime_channel: team_member_incorrect_crime_channel,
          team_member_incorrect_crime_roles: team_member_incorrect_crime_roles
          # enabled: true
        } = config
      ) do
    messages = [
      %Nostrum.Struct.Message{
        channel_id: team_member_incorrect_crime_channel,
        # TODO: Add mention and assigns for user that needs to join
        content: Tornium.Utils.roles_to_string(team_member_incorrect_crime_roles),
        embeds: [
          %Nostrum.Struct.Embed{
            title: "Incorrect OC Joined",
            description: """
            #{member_name} [#{member_id}] has joined a #{incorrect_oc_name} OC (ID #{incorrect_oc_id}) but was \
            supposed to join the #{oc_slot_type} ##{oc_slot_index} slot of the assigned #{assigned_oc_name} OC \
            (ID #{assigned_oc_id}). Join the assigned OC through the button below. \
            """,
            color: Tornium.Discord.Constants.colors()[:error],
            footer: %Nostrum.Struct.Embed.Footer{text: "Team ID: #{team_guid}"}
          }
        ],
        components: [
          %Nostrum.Struct.Component{
            type: 1,
            components: [
              %Nostrum.Struct.Component{
                type: 2,
                style: 5,
                label: "Assigned OC",
                url: "https://www.torn.com/factions.php?step=your&type=1#/tab=crimes&crimeId=#{assigned_oc_id}"
              }
            ]
          }
        ]
      }
      | messages
    ]

    render_feature(messages, :team_member_incorrect_crime, remaining_incorrect_crimes, config)
  end

  def render_feature(
        messages,
        :assigned_team,
        [
          {%Tornium.Schema.OrganizedCrimeTeam{name: team_name, guid: team_guid, members: team_members} = _team,
           %Tornium.Schema.OrganizedCrime{oc_name: oc_name, oc_id: oc_id} = _crime}
          | remaining_slots
        ] =
          _slots,
        %Tornium.Schema.ServerOCConfig{
          assigned_team_channel: assigned_team_channel,
          assigned_team_roles: assigned_team_roles
          # enabled: true,
        } = config
      )
      when is_list(messages) and not is_nil(assigned_team_channel) do
    messages =
      [
        %Nostrum.Struct.Message{
          channel_id: assigned_team_channel,
          content: Tornium.Utils.roles_to_string(assigned_team_roles, assigns: team_member_discord_ids(team_members)),
          embeds: [
            %Nostrum.Struct.Embed{
              title: "OC Team Assigned",
              description: "The #{team_name} OC team has been assigned to an #{oc_name} OC.",
              color: Tornium.Discord.Constants.colors()[:good],
              footer: %Nostrum.Struct.Embed.Footer{text: "Team ID: #{team_guid} | OC ID: #{oc_id}"}
            }
          ],
          components: [
            %Nostrum.Struct.Component{
              type: 1,
              components: [
                %Nostrum.Struct.Component{
                  type: 2,
                  style: 5,
                  label: "Assigned OC",
                  url: "https://www.torn.com/factions.php?step=your&type=1#/tab=crimes&crimeId=#{oc_id}"
                }
              ]
            }
          ]
        }
        | messages
      ]

    render_feature(messages, :assigned_team, remaining_slots, config)
  end

  def render_feature(messages, _state_element, _slots, %Tornium.Schema.ServerOCConfig{} = _config) do
    messages
  end

  @spec team_member_discord_ids(members :: [Tornium.Schema.OrganizedCrimeTeamMember.t()]) :: [non_neg_integer()]
  defp team_member_discord_ids([%Tornium.Schema.OrganizedCrimeTeamMember{} = _member | _remaining_members] = members) do
    user_ids =
      members
      |> Enum.map(fn
        %Tornium.Schema.OrganizedCrimeTeamMember{user_id: user_id} when is_integer(user_id) -> user_id
        _ -> nil
      end)
      |> Enum.reject(&is_nil/1)

    Tornium.Schema.User
    |> where([u], u.tid in ^user_ids)
    |> select([u], u.discord_id)
    |> Repo.all()
    |> Enum.reject(&is_nil/1)
    |> Enum.map(fn discord_id -> {:user, discord_id} end)
  end

  defp team_member_discord_ids([] = _members) do
    # Fallback to avoid making unnecessary DB requests when there are no team members set up
    []
  end
end
