defmodule Tornium.Repo.Migrations.AddServerOdConfig do
  use Ecto.Migration

  def change do
    create_if_not_exists table("server_overdose_config", primary_key: false) do
      add :guid, :binary_id, primary_key: true, autogenerate: true
      add :server_id, references(:server, column: :sid, type: :bigint), null: false
      add :faction_id, references(:faction, column: :tid, type: :integer), null: false

      add :enabled, :boolean, default: false, null: false
      add :channel, :bigint, default: nil, null: true
    end

    create_if_not_exists unique_index(:server_overdose_config, [:server_id, :faction_id])
  end
end
