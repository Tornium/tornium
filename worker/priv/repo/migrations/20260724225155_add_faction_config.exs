defmodule Tornium.Repo.Migrations.AddFactionConfig do
  use Ecto.Migration

  def change do
    create_if_not_exists table("faction_config", primary_key: false) do
      add :guid, :binary_id, primary_key: true, autogenerate: true
      add :faction_id, references(:faction, column: :tid, type: :integer), null: false

      add :ts_stats_enabled, :boolean, default: true, null: false
    end

    create unique_index("faction_config", [:faction_id])
  end
end
