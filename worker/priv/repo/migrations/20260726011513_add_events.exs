defmodule Tornium.Repo.Migrations.AddEvents do
  use Ecto.Migration

  def change do
    # We need the btree_gist extension for the exclusion constraints to prevent overlapping events
    execute("CREATE EXTENSION IF NOT EXISTS btree_gist", "DROP EXTENSION IF EXISTS btree_gist")

    # --- Torn Event ---
    create_if_not_exists table("torn_event", primary_key: false) do
      add :guid, :binary_id, primary_key: true, autogenerate: true
      add :title, :string, null: false
      add :description, :text, null: false
      add :type, :string, null: false

      add :start_timestamp, :utc_datetime, null: false
      add :end_timestamp, :utc_datetime, null: false
      add :configurable, :boolean, default: false, null: false
    end
    create_if_not_exists index("torn_event", [:start_timestamp, :end_timestamp])

    # --- Steadfast Event ---
    create_if_not_exists table("steadfast_event", primary_key: false) do
      add :guid, :binary_id, primary_key: true, autogenerate: true
      add :faction_id, references(:faction, column: :tid, type: :integer), null: false

      add :strength, :integer, default: 0, null: true
      add :defense, :integer, default: 0, null: true
      add :speed, :integer, default: 0, null: true
      add :dexterity, :integer, default: 0, null: true

      add :start_timestamp, :utc_datetime, null: false
      add :end_timestamp, :utc_datetime, null: false
    end
    create_if_not_exists index("steadfast_event", [:faction_id])
    create_if_not_exists index("steadfast_event", [:start_timestamp, :end_timestamp])
    create constraint(
      "steadfast_event",
      :steadfast_event_no_overlap,
      exclude: ~s|gist (faction_id WITH =, tsrange(start_timestamp, end_timestamp) WITH &&)|
    )

    # --- RW Event ---
    create_if_not_exists table("rw_event", primary_key: false) do
      add :guid, :binary_id, primary_key: true, autogenerate: true
      add :faction_id, references(:faction, column: :tid, type: :integer), null: false

      add :enlistment_timestamp, :utc_datetime, null: false
    end
    create_if_not_exists unique_index("rw_event", [:faction_id, :enlistment_timestamp])

    # --- Custom User Event ---

    # --- Custom Faction Event ---

    # --- Chain Event --
    create_if_not_exists table("chain_event", primary_key: false) do
      add :guid, :binary_id, primary_key: true, autogenerate: true
      add :faction_id, references(:faction, column: :tid, type: :integer), null: false

      # add :chain_id, references(:chain, column: :id, type: :integer), default: nil, null: true
      add :expected_chain_length, :integer

      add :start_timestamp, :utc_datetime, null: false
      add :end_timestamp, :utc_datetime, null: false
    end
    create_if_not_exists index("chain_event", [:faction_id])
    create_if_not_exists index("chain_event", [:start_timestamp, :end_timestamp])
    create constraint(
      "chain_event",
      :chain_event_no_overlap,
      exclude: ~s|gist (faction_id WITH =, tsrange(start_timestamp, end_timestamp) WITH &&)|
    )
  end
end
