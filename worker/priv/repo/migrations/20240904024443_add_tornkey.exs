defmodule Tornium.Repo.Migrations.AddTornkey do
  use Ecto.Migration

  def up do
    create_if_not_exists table("tornkey", primary_key: false) do
      add :guid, :binary_id, primary_key: true
      add :api_key, :string, size: 16, null: false, unique: true
      add :user_id, references(:user, column: :tid, type: :integer)
      add :default, :boolean, default: false, null: false
      add :disabled, :boolean, default: false, null: false
      add :paused, :boolean, default: false, null: false
      add :access_level, :integer, default: nil, null: true
    end
    create unique_index(:tornkey, [:guid])
    create unique_index(:tornkey, [:api_key])
  end

  def down do
    drop table("tornkey")
  end
end
