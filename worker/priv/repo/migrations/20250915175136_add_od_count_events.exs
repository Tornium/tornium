defmodule Tornium.Repo.Migrations.AddOdCountEvents do
  use Ecto.Migration

  def change do
    create_if_not_exists table("overdose_count", primary_key: false) do
      add :guid, :binary_id, primary_key: true, autogenerate: true
      add :faction_id, references(:faction, column: :tid, type: :integer), null: false
      add :user_id, references(:user, column: :tid, type: :integer), null: false

      add :count, :integer, default: 0, null: false
      add :updated_at, :utc_datetime, default: fragment("now()"), null: false
    end

    create_if_not_exists table("overdose_event", primary_key: false) do
      add :guid, :binary_id, primary_key: true, autogenerate: true
      add :faction_id, references(:faction, column: :tid, type: :integer), null: false
      add :user_id, references(:user, column: :tid, type: :integer), null: false

      add :created_at, :utc_datetime, null: false
      add :drug, :string, default: nil, null: true
    end

    create_if_not_exists unique_index(:overdose_count, [:faction_id, :user_id])
    create_if_not_exists index(:overdose_event, [:faction_id, :user_id])
  end
end
