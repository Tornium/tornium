defmodule Tornium.Repo.Migrations.FactionPositionFk do
  use Ecto.Migration

  def up do
    rename table("faction_position"), :faction_tid, to: :faction_id

    alter table("faction_position") do
      modify :faction_id, references(:faction, column: :tid, type: :integer), null: false
    end

    create_if_not_exists index(:faction_position, [:faction_id])
    create_if_not_exists unique_index(:faction_position, [:faction_id, :name])
  end

  def down do
    drop_if_exists index(:faction_position, [:faction_id])
    drop_if_exists unique_index(:faction_position, [:faction_id, :name])

    alter table("faction_position") do
      modify :faction_id, :integer
    end

    rename table("faction_position"), :faction_id, to: :faction_tid
  end
end
