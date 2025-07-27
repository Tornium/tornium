defmodule Tornium.Repo.Migrations.AddTriggerTable do
  use Ecto.Migration

  def up do
    create_if_not_exists table("notification_trigger", primary_key: false) do
      add :tid, :binary_id, primary_key: true
      add :name, :string, null: false
      add :description, :text, default: "", null: false
      add :owner_id, references(:user, column: :tid, type: :integer), null: false

      add :cron, :string, default: "* * * * *", null: false
      add :next_execution, :utc_datetime, default: nil, null: true

      add :resource, :string, null: false  # Enum is represented as a string in the database
      add :selections, {:array, :string}, default: [], null: false
      add :code, :text, default: "", null: false
      add :parameters, :map, default: %{}, null: false

      add :message_type, :string, null: false  # Enum is represented as a string in the database
      add :message_template, :text, null: false

      add :restricted_data, :boolean, default: false, null: false
      add :official, :boolean, default: false, null: false
    end

    create unique_index(:notification_trigger, [:tid])
    create unique_index(:notification_trigger, [:owner_id, :name])

    create_if_not_exists table("notification", primary_key: false) do
      add :nid, :binary_id, primary_key: true
      add :trigger_id, references(:notification_trigger, column: :tid, type: :binary_id), null: false
      add :user_id, references(:user, column: :tid, type: :integer), null: false
      add :enabled, :boolean, default: true, null: false

      add :server_id, references(:server, column: :sid, type: :bigint), null: true
      add :channel_id, :bigint, default: nil, null: true
      add :message_id, :bigint, default: nil, null: true

      add :resource_id, :integer, default: nil, null: true
      add :one_shot, :boolean, default: true, null: false
      add :parameters, :map, default: %{}, null: false

      add :error, :text, default: nil, null: true
      add :previous_state, :map, default: %{}, null: false
    end

    create_if_not_exists table("server_notifications_config") do
      add :server_id, references(:server, column: :sid, type: :bigint), null: false
      add :enabled, :boolean, default: false, null: false
      add :log_channel, :bigint, default: nil, null: true
    end

    create unique_index(:server_notifications_config, :server_id)

    # Will cause a duplicate_object constraint error without dropping the constraint
    # See https://github.com/elixir-ecto/ecto/issues/722
    drop_if_exists constraint("server", "notifications_config_id_fkey")
    alter table("server") do
      add_if_not_exists :notifications_config_id, references(:server_notifications_config, column: :id, type: :id)
    end
  end

  def down do
    drop_if_exists table("notification")
    drop_if_exists table("notification_trigger")

    drop_if_exists constraint("server", "notifications_config_id_fkey")
    alter table("server") do
      Ecto.Migration.remove_if_exists(:notifications_config_id, references(:server_notifications_config, column: :id, type: :id))
    end

    drop_if_exists table("server_notifications_config")
  end
end
