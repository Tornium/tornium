defmodule Tornium.Repo.Migrations.AddOCExtraRange do
  use Ecto.Migration

  def change do
    alter table("server_oc_config") do
      add :extra_range_channel, :bigint, default: nil, null: true
      add :extra_range_roles, {:array, :bigint}, default: [], null: false
      add :extra_range_global_min, :integer, default: 0, null: false
      add :extra_range_global_max, :integer, default: 100, null: false
    end

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
