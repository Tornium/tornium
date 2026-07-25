defmodule Tornium.Repo.Migrations.AddVerificationLogs do
  use Ecto.Migration

  def change do
    create_if_not_exists table("verification_log", primary_key: false) do
      add :guid, :binary_id, primary_key: true, autogenerate: true
      add :server_id, references(:server, column: :sid, type: :bigint, on_delete: :delete_all), null: false
      add :discord_id, :bigint, default: nil, null: true
      add :user_id, references(:user, column: :tid, type: :integer, on_delete: :delete_all), default: nil, null: true

      add :old_nickname, :string, default: nil, null: true
      add :new_nickname, :string, default: nil, null: true
      add :roles_added, {:array, :bigint}, default: [], null: false
      add :roles_removed, {:array, :bigint}, default: [], null: false

      add :error_type, :string, default: nil, null: true
      add :error_code, :integer, default: nil, null: true
      add :error_message, :string, default: nil, null: true

      add :timestamp, :utc_datetime, null: false
    end

    create_if_not_exists index(:verification_log, [:server_id, desc: :timestamp])
  end
end
