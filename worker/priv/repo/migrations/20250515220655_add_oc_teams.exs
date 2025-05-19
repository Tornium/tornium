defmodule Tornium.Repo.Migrations.AddOcTeams do
  use Ecto.Migration

  def change do
    create_if_not_exists table("organized_crime_team", primary_key: false) do
      add :guid, :binary_id, primary_key: true, autogenerate: true
      add :oc_name, :string, null: false
      add :name, :string, null: false
      add :faction_id, references(:faction, column: :tid, type: :integer), null: false
    end

    create_if_not_exists table("organized_crime_team_member", primary_key: false) do
      add :guid, :binary_id, primary_key: true, autogenerate: true
      add :user_id, references(:user, column: :tid, type: :integer), null: false
      add :team_id, references(:organized_crime_team, column: :guid, type: :binary_id), null: false

      add :slot_type, :string, null: false
      add :slot_index, :integer, null: false
    end

    alter table("organized_crime_new") do
      add :assigned_team_id, references(:organized_crime_team, column: :guid, type: :binary_id), default: nil, null: true
    end

    create_if_not_exists unique_index(:organized_crime_team_member, [:user_id, :team_id])
  end
end
