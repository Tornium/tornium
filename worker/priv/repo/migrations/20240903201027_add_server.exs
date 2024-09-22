defmodule Tornium.Repo.Migrations.AddServer do
  use Ecto.Migration

  def up do
    create_if_not_exists table("server", primary_key: false) do
      add :sid, :bigint, primary_key: true
      add :name, :string, null: false
      add :admins, {:array, :integer}, default: [], null: false
      add :icon, :string, null: true, default: nil

      add :factions, {:array, :integer}, default: [], null: false

      add :verify_enabled, :boolean, default: false, null: false
      add :auto_verify_enabled, :boolean, default: false, null: false
      add :gateway_verify_enabled, :boolean, default: false, null: false
      add :verify_template, :string, default: "{{ name }} [{{ tid }}]"
      add :verified_roles, {:array, :bigint}, default: [], null: false
      add :exclusion_roles, {:array, :bigint}, default: [], null: false
      add :faction_verify, :map, default: %{}, null: false
      add :verify_log_channel, :bigint, default: 0, null: false
      add :verify_jail_channel, :bigint, default: 0, null: false

      add :banking_config, :map, default: %{}, null: false

      add :armory_enabled, :boolean, default: false, null: false
      add :armory_config, :map, default: %{}, null: false

      add :assist_channel, :bigint, default: 0, null: false
      add :assist_factions, {:array, :integer}, default: [], null: false
      add :assist_smoker_roles, {:array, :bigint}, default: [], null: false
      add :assist_tear_roles, {:array, :bigint}, default: [], null: false
      add :assist_l0_roles, {:array, :bigint}, default: [], null: false
      add :assist_l1_roles, {:array, :bigint}, default: [], null: false
      add :assist_l2_roles, {:array, :bigint}, default: [], null: false
      add :assist_l3_roles, {:array, :bigint}, default: [], null: false

      add :oc_config, :map, default: %{}, null: false
    end

    create unique_index(:server, [:sid])
  end

  def down do
    drop table("server")
  end
end
