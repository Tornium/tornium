defmodule Tornium.Repo.Migrations.AddOcTeamRequiredSpawnAt do
  use Ecto.Migration

  def change do
    alter table("organized_crime_team") do
      add :required_spawn_at, :utc_datetime, default: nil, null: true
    end
  end
end
