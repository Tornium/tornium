defmodule Tornium.Repo.Migrations.AddOcConfig do
  use Ecto.Migration

  def up do
    create_if_not_exists table("server_oc_config", primary_key: false) do
      add :server_id, references(:server, column: :sid, type: :bigint), primary_key: true
      add :faction_id, references(:faction, column: :tid, type: :integer), primary_key: true
      add :enabled, :boolean, default: false, null: false

      add :tool_channel, :bigint, default: nil, null: true
      add :tool_roles, {:array, :bigint}, default: [], null: false
      add :tool_crimes, {:array, :string}, default: [], null: false

      add :delayed_channel, :bigint, default: nil, null: true
      add :delayed_roles, {:array, :bigint}, default: [], null: false
      add :delayed_crimes, {:array, :string}, default: [], null: false
    end
  end
  
  def down do
    drop_if_exists table("server_oc_config")
  end
end
