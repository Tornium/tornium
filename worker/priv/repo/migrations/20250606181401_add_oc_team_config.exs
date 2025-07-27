defmodule Tornium.Repo.Migrations.AddOcTeamConfig do
  use Ecto.Migration

  def change do
    alter table("server_oc_config") do
      add_if_not_exists :team_spawn_required_channel, :bigint, default: nil, null: true
      add_if_not_exists :team_spawn_required_roles, {:array, :bigint}, default: [], null: false

      add_if_not_exists :team_member_join_required_channel, :bigint, default: nil, null: true
      add_if_not_exists :team_member_join_required_roles, {:array, :bigint}, default: [], null: false

      add_if_not_exists :team_member_incorrect_crime_channel, :bigint, default: nil, null: true
      add_if_not_exists :team_member_incorrect_crime_roles, {:array, :bigint}, default: [], null: false

      add_if_not_exists :team_incorrect_member_channel, :bigint, default: nil, null: true
      add_if_not_exists :team_incorrect_member_roles, {:array, :bigint}, default: [], null: false

      add_if_not_exists :team_member_incorrect_slot_channel, :bigint, default: nil, null: true
      add_if_not_exists :team_member_incorrect_slot_roles, {:array, :bigint}, default: [], null: false

      add_if_not_exists :assigned_team_channel, :bigint, default: nil, null: true
      add_if_not_exists :assigned_team_roles, {:array, :bigint}, default: [], null: false
    end
  end
end
