defmodule Tornium.Repo.Migrations.AddWarRetalToggle do
  use Ecto.Migration

  def change do
    create_if_not_exists table("serverattackconfig", primary_key: false) do
      add :faction_id, references(:faction, column: :tid, type: :integer), null: false, primary_key: true
      add :server_id, references(:server, column: :sid, type: :bigint), null: false, primary_key: true

      add :retal_channel, :bigint, default: nil, null: true
      add :retal_roles, {:array, :bigint}, default: [], null: false

      add :chain_bonus_channel, :bigint, default: nil, null: true
      add :chain_bonus_roles, {:array, :bigint}, default: [], null: false
      add :chain_bonus_length, :integer, default: 100, null: false

      add :chain_alert_channel, :bigint, default: nil, null: true
      add :chain_alert_roles, {:array, :bigint}, default: [], null: false
    end

    alter table("serverattackconfig") do
      add :retal_wars, :boolean, default: false, null: false
    end
  end
end
