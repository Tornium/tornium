defmodule Tornium.Repo.Migrations.AddOcGraph do
  use Ecto.Migration

  def change do
    create_if_not_exists table("organized_crime_graph_node", primary_key: false) do
      add :guid, :binary_id, primary_key: true
      add :oc_type_id, references(:organized_crime_type, column: :guid, type: :binary_id), null: false

      add :scene_id, :integer, null: false
      add :scene_slug, :string, null: false
      add :terminal, :boolean, default: false, null: false

      add :last_seen_at, :utc_datetime, null: false
      add :last_seen_by_id, references(:user, column: :tid, type: :integer), null: false
      add :last_seen_in_id, references(:organized_crime, column: :oc_id, type: :integer), null: false
    end
    create_if_not_exists unique_index(:organized_crime_graph_node, [:oc_type_id, :scene_id, :scene_slug])

    create_if_not_exists table("organized_crime_graph_node_variant", primary_key: false) do
      add :guid, :binary_id, primary_key: true

      add :node_id, references(:organized_crime_graph_node, column: :guid, type: :binary_id), null: false
      add :text, :string, null: false
      add :effective_weight, :float, null: false, default: 1.0

      add :last_seen_at, :utc_datetime, null: false
      add :last_seen_by_id, references(:user, column: :tid, type: :integer), null: false
      add :last_seen_in_id, references(:organized_crime, column: :oc_id, type: :integer), null: false
    end
    create_if_not_exists unique_index(:organized_crime_graph_node_variant, [:node_id, :text])

    create_if_not_exists table("organized_crime_graph_edge", primary_key: false) do
      add :guid, :binary_id, primary_key: true

      add :success, :boolean, null: false
      add :from_node_id, references(:organized_crime_graph_node, column: :guid, type: :binary_id), null: false
      add :to_node_id, references(:organized_crime_graph_node, column: :guid, type: :binary_id), null: false

      add :effective_weight, :float, null: false, default: 1.0

      add :last_seen_at, :utc_datetime, null: false
      add :last_seen_by_id, references(:user, column: :tid, type: :integer), null: false
      add :last_seen_in_id, references(:organized_crime, column: :oc_id, type: :integer), null: false
    end
    create_if_not_exists unique_index(:organized_crime_graph_edge, [:from_node_id, :to_node_id, :success])

    create_if_not_exists table("organized_crime_graph_terminal_reward", primary_key: false) do
      add :guid, :binary_id, primary_key: true
      add :node_id, references(:organized_crime_graph_node, column: :guid, type: :binary_id), null: false

      add :respect, :map, default: nil, null: true
      add :money, :map, default: nil, null: true
      add :item_sets, :map, default: nil, null: true

      add :last_seen_at, :utc_datetime, null: false
      add :last_seen_by_id, references(:user, column: :tid, type: :integer), null: false
      add :last_seen_in_id, references(:organized_crime, column: :oc_id, type: :integer), null: false
    end
    create_if_not_exists unique_index(:organized_crime_graph_terminal_reward, [:node_id])
    create constraint(
      :organized_crime_graph_terminal_reward,
      :terminal_reward_payout,
      check: """
      (respect IS NULL AND money is NULL AND item_sets IS NULL)
      OR (respect IS NOT NULL AND (money is NULL) <> (item_sets IS NULL))
      """
    )
    create constraint(
      :organized_crime_graph_terminal_reward,
      :terminal_reward_valid_json,
      check: """
      (respect IS NULL OR jsonb_typeof(respect) = 'array')
      AND (money IS NULL OR jsonb_typeof(money) = 'array')
      AND (item_sets IS NULL OR jsonb_typeof(item_sets) = 'array')
      """
    )

    alter table("organized_crime") do
      add :scenario_ingested_at, :utc_datetime, default: nil, null: true
    end
  end
end
