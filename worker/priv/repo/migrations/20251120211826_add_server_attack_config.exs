defmodule Tornium.Repo.Migrations.AddServerAttackConfig do
  use Ecto.Migration
  
  def change do
    create_if_not_exists table("server_attack_config", primary_key: false) do
      add :faction_id, references(:faction, column: :tid, type: :integer), primary_key: true
      add :server_id, references(:server, column: :sid, type: :bigint), primary_key: true

      add :retal_channel, :bigint, default: nil, null: true
      add :retal_roles, {:array, :bigint}, default: [], null: false
      add :retal_wars, :boolean, default: false, null: false

      add :chain_bonus_channel, :bigint, default: nil, null: true
      add :chain_bonus_roles, {:array, :bigint}, default: [], null: false
      add :chain_bonus_length, :integer, default: 100, null: false

      add :chain_alert_channel, :bigint, default: nil, null: true
      add :chain_alert_roles, {:array, :bigint}, default: [], null: false
      add :chain_alert_minimum, :integer, default: 60, null: false
    end
  end
end
