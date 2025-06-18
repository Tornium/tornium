defmodule Tornium.Repo.Migrations.AddOcAssignedAt do
  use Ecto.Migration

  def change do
    alter table("organized_crime_new") do
      add :assigned_team_at, :utc_datetime, default: nil, null: true
    end
  end
end
