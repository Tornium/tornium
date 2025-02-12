defmodule Tornium.Repo.Migrations.AddOc do
  use Ecto.Migration

  def up do
    create_if_not_exists table("item", primary_key: false) do
      add :tid, :integer, primary_key: true
      add :name, :string, null: false
      add :description, :text, default: nil, null: true
      add :item_type, :string, default: nil, null: true
      add :market_value, :bigint, default: 0, null: false
      add :circulation, :bigint, default: 0, null: false
    end

    alter table("faction") do
      add_if_not_exists :has_migrated_oc, :boolean, default: false, null: false
    end

    create_if_not_exists table("organized_crime_new", primary_key: false) do
      add :oc_id, :integer, primary_key: true
      add :oc_name, :string, null: false
      add :oc_difficulty, :integer, null: false
      add :faction_id, references(:faction, column: :tid, type: :integer)
      add :status, :string, null: false  # Enum is represented as a string in the database
      add :created_at, :utc_datetime, null: false
      add :planning_started_at, :utc_datetime, default: nil, null: true
      add :ready_at, :utc_datetime, default: nil, null: true
      add :expires_at, :utc_datetime, null: false
      add :executed_at, :utc_datetime, default: nil, null: true
    end

    create_if_not_exists table("organized_crime_slot", primary_key: false) do
      add :id, :binary_id, primary_key: true
      add :oc_id, references(:organized_crime_new, column: :oc_id, type: :integer)
      add :slot_index, :integer, null: false
      add :crime_position, :string, null: false
      add :user_id, references(:user, column: :tid, type: :integer)
      add :user_success_chance, :integer, default: nil, null: true
      add :item_required_id, references(:item, column: :tid, type: :integer), default: nil, null: true
      add :item_available, :boolean, default: false, null: false
      add :delayer, :boolean, default: false, null: false
      add :delayed_reason, :string, default: nil, null: true
      add :sent_tool_notification, :boolean, default: false, null: false
    end

    create_if_not_exists unique_index(:organized_crime_slot, [:oc_id, :slot_index, :user_id])
  end

  def down do
    drop_if_exists table("organized_crime_slot"), mode: :cascade
    drop_if_exists table("organized_crime_new")
    drop_if_exists table("item")

    alter table("faction") do
      remove_if_exists :has_migrated_oc
    end
  end
end
