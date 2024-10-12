defmodule Tornium.Repo.Migrations.AddTriggerTable do
  use Ecto.Migration

  def up do
    create_if_not_exists table("notification_trigger", primary_key: false) do
      add :tid, :binary_id, primary_key: true
      add :name, :string, default: "", null: false
      add :description, :string, default: "", null: false
      add :owner_id, references(:user, column: :tid, type: :integer)

      add :resource, :string  # Enum is represented as a string in the database
      add :selections, {:array, :string}, default: [], null: false
      add :code, :string, default: "", null: false

      add :public, :boolean, default: false, null: false
      add :official, :boolean, default: false, null: false
    end

    create unique_index(:notification_trigger, [:tid])

    create_if_not_exists table("notification", primary_key: false) do
      add :nid, :binary_id, primary_key: true
      add :trigger_id, references(:notification_trigger, column: :tid, type: :binary_id)
      add :user_id, references(:user, column: :tid, type: :integer)

      add :resource_id, :integer, default: nil, null: true
      add :one_shot, :boolean, default: true, null: false

      add :cron, :string, default: "* * * * *", null: false
      add :next_execution, :utc_datetime, default: nil, null: true

      add :error, :string, default: nil, null: true
      add :previous_state, :map, default: %{}, null: false
    end

    create unique_index(:notification, [:nid])
  end

  def down do
    drop_if_exists table("notification")
    drop_if_exists table("notification_trigger")
  end
end
