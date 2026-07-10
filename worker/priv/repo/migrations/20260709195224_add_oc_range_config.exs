defmodule Tornium.Repo.Migrations.AddOcRangeConfig do
  use Ecto.Migration

  def up do
    rename table("server_oc_range_config"), to: table("server_oc_range_config_back")

    create_if_not_exists table("server_oc_range_config", primary_key: false) do
      add :guid, :binary_id, primary_key: true, autogenerate: true
      add :server_oc_config_id, references(:server_oc_config, column: :guid, type: :binary_id), null: false

      add :oc_type_id, references(:organized_crime_type, column: :guid, type: :binary_id), null: false
      add :oc_slot_type_id, references(:organized_crime_slot_type, column: :guid, type: :binary_id), null: false

      add :minimum, :integer, default: 0, null: false
      add :maximum, :integer, default: 100, null: false
    end
    create unique_index("server_oc_range_config", [:server_oc_config_id, :oc_type_id, :oc_slot_type_id])

    execute("""
    INSERT INTO server_oc_range_config
      (guid, server_oc_config_id, oc_type_id, oc_slot_type_id, minimum, maximum)
    SELECT
      gen_random_uuid(),
      c.server_oc_config_id,
      oc_type.guid,
      oc_slot_type.guid,
      c.minimum,
      c.maximum
    FROM server_oc_range_config_back AS c
    INNER JOIN organized_crime_type AS oc_type
      ON oc_type.name = c.oc_name
    INNER JOIN organized_crime_slot_type AS oc_slot_type
      ON oc_slot_type.oc_type_id = oc_type.guid
    """)
  end

  def down do
    drop table("server_oc_range_config")
    rename table("server_oc_range_config_back"), to: table("server_oc_range_config")

    create_if_not_exists table("server_oc_range_config", primary_key: false) do
      add :guid, :binary_id, primary_key: true, autogenerate: true
      add :server_oc_config_id, references(:server_oc_config, column: :guid, type: :binary_id), null: false
      add :oc_name, :string, null: false
      add :minimum, :integer, default: 0, null: false
      add :maximum, :integer, default: 100, null: false
    end

    create_if_not_exists unique_index(:server_oc_range_config, [:server_oc_config_id, :oc_name])
  end
end
