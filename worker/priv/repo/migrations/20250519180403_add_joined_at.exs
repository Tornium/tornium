defmodule Tornium.Repo.Migrations.AddJoinedAt do
  use Ecto.Migration

  def change do
    alter table("organized_crime_slot") do
      add :user_joined_at, :utc_datetime, default: nil, null: true
    end
  end
end
