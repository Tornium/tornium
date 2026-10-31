defmodule Tornium.Repo.Migrations.AddChains do
  use Ecto.Migration

  def change do
    create_if_not_exists table("chain", primary_key: false) do
      add :chain_id, :integer, primary_key: true
      add :faction_id, references(:faction, column: :tid, type: :integer), null: false
      add :length, :integer, null: false
      add :start_timestamp, :utc_datetime, null: false
      add :end_timestamp, :utc_datetime, default: nil, null: true
    end

    create_if_not_exists index(:chain, [:faction_id, :start_timestamp])
  end
end
