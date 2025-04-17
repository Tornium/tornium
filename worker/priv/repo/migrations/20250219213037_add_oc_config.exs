defmodule Tornium.Repo.Migrations.AddOcConfig do
  use Ecto.Migration

  def change do
    create_if_not_exists table("server_oc_config", primary_key: false) do
      add :guid, :binary_id, primary_key: true, autogenerate: true
      add :server_id, references(:server, column: :sid, type: :bigint), null: false
      add :faction_id, references(:faction, column: :tid, type: :integer), null: false
      add :enabled, :boolean, default: false, null: false

      add :tool_channel, :bigint, default: nil, null: true
      add :tool_roles, {:array, :bigint}, default: [], null: false
      add :tool_crimes, {:array, :string}, default: [], null: false

      add :delayed_channel, :bigint, default: nil, null: true
      add :delayed_roles, {:array, :bigint}, default: [], null: false
      add :delayed_crimes, {:array, :string}, default: [], null: false
    end

    create_if_not_exists unique_index(:server_oc_config, [:server_id, :faction_id])
  end
end
