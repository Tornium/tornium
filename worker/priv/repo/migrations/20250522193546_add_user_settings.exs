defmodule Tornium.Repo.Migrations.AddUserSettings do
  use Ecto.Migration

  def change do
    create_if_not_exists table("user_settings", primary_key: false) do
      add :guid, :binary_id, primary_key: true, autogenerate: true
      add :user_id, references(:user, column: :tid, type: :integer), null: true
      add :cpr_enabled, :boolean, default: true, null: false
    end

    alter table("user") do
      add :settings_id, references(:user_settings, column: :guid, type: :binary_id), default: nil, null: true
    end

    create_if_not_exists unique_index(:user_settings, [:user_id])
  end
end
