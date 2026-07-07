defmodule Tornium.Repo.Migrations.AddOcType do
  use Ecto.Migration

  def change do
    create_if_not_exists table("organized_crime_type", primary_key: false) do
      add :guid, :binary_id, primary_key: true, autogenerate: true
      add :name, :string, null: false
      add :description, :binary, null: false
      add :difficulty, :integer, null: false
      add :spawn_level, :integer, null: false
      add :prerequisite_id, references(:organized_crime_type, column: :guid, type: :binary_id), default: nil, null: true
    end
    create_if_not_exists unique_index(:organized_crime_type, [:name])

    create_if_not_exists table("organized_crime_slot_type", primary_key: false) do
      add :guid, :binary_id, primary_key: true, autogenerate: true
      add :oc_type_id, references(:organized_crime_type, column: :guid, type: :binary_id), null: false
      
      add :name, :string, null: false
      add :number, :integer, null: false
      add :index, :integer, null: false

      add :required_item_id, references(:item, column: :tid, type: :integer), default: nil, null: true
      add :required_item_consumed, :boolean, default: nil, null: true
    end
    create_if_not_exists unique_index(:organized_crime_slot_type, [:oc_type_id, :name, :number])
    create_if_not_exists unique_index(:organized_crime_slot_type, [:oc_type_id, :index])
  end
end
