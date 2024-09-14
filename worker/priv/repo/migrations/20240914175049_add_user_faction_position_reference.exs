defmodule Tornium.Repo.Migrations.AddUserFactionPositionReference do
  use Ecto.Migration

  def change do
    alter table("user") do
      add :faction_position_id, references(:faction_position, column: :pid, type: :binary_id)
    end
  end
end
