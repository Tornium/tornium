defmodule Tornium.Repo.Migrations.RemoveOcTeam do
  use Ecto.Migration

  def change do
    alter table("organized_crime") do
      remove :assigned_team_id
      remove :assigned_team_at
    end

    alter table("server_oc_config") do
      remove :team_spawn_required_channel
      remove :team_spawn_required_roles
      remove :team_member_join_required_channel
      remove :team_member_join_required_roles
      remove :team_member_incorrect_crime_channel
      remove :team_member_incorrect_crime_roles
      remove :team_incorrect_member_channel
      remove :team_incorrect_member_roles
      remove :team_member_incorrect_slot_channel
      remove :team_member_incorrect_slot_roles
      remove :assigned_team_channel
      remove :assigned_team_roles
    end

    drop table("organized_crime_team_member")
    drop table("organized_crime_team")
  end
end
