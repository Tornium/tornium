defmodule Tornium.Repo.Migrations.AddUser do
  use Ecto.Migration

  def up do
    create_if_not_exists table("user", primary_key: false) do
      add :tid, :integer, primary_key: true
      add :name, :string, size: 15, default: "", null: false
      add :level, :integer, null: false
      add :discord_id, :bigint, default: nil, null: true
      # Skip personal stats for later

      add :battlescore, :float, default: nil, null: true
      add :strength, :bigint, default: nil, null: true
      add :defense, :bigint, default: nil, null: true
      add :speed, :bigint, default: nil, null: true
      add :dexterity, :bigint, default: nil, null: true

      # Skip faction for later
      add :faction_aa, :boolean, default: false, null: false
      # skip faction position for later

      add :status, :string, default: nil, null: true
      add :last_action, :utc_datetime_usec, default: nil, null: true
      
      add :last_refresh, :utc_datetime_usec, default: nil, null: true
      add :last_attacks, :utc_datetime_usec, default: nil, null: true
      add :battlescore_update, :utc_datetime_usec, default: nil, null: true

      add :security, :integer, default: nil, null: true
      add :otp_secret, :string, default: nil, null: true
      add :otp_backups, {:array, :string}, default: [], null: false
    end

    create unique_index(:user, [:tid])
  end

  def down do
    drop table("user")
  end
end
