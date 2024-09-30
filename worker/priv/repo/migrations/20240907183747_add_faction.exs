defmodule Tornium.Repo.Migrations.AddFaction do
  use Ecto.Migration

  def up do
    create_if_not_exists table("faction", primary_key: false) do
      add :tid, :integer, primary_key: true
      add :name, :string, size: 50, null: true
      add :tag, :string, size: 8, null: true
      add :respect, :integer, null: true
      add :capacity, :integer, null: true
      add :leader_id, references(:user, column: :tid, type: :integer)
      add :coleader_id, references(:user, column: :tid, type: :integer)

      add :guild_id, references(:server, column: :sid, type: :bigint)

      add :stats_db_enabled, :boolean, default: true, null: false
      add :stats_db_global, :boolean, default: true, null: false

      add :od_channel, :integer, null: true
      add :od_data, :map, null: true

      add :last_members, :utc_datetime_usec, null: true
      add :last_attacks, :utc_datetime_usec, null: true
    end
    create unique_index(:faction, [:tid])
    create unique_index(:faction, [:leader_id])
    create unique_index(:faction, [:coleader_id])
    create unique_index(:faction, [:guild_id])
  end

  def down do
    drop table("faction")
  end
end
