defmodule Tornium.Repo.Migrations.AddUserFactionReference do
  use Ecto.Migration

  def change do
    alter table("user") do
      add :faction_id, references(:faction, column: :tid, type: :integer)
    end
  end
end
