defmodule Tornium.Repo.Migrations.AddOcCprTable do
  use Ecto.Migration

  def change do
    create_if_not_exists table("organized_crime_cpr", primary_key: false) do
      add :guid, :binary_id, primary_key: true, autogenerate: true
      add :user_id, references(:user, column: :tid, type: :integer), null: true
      add :oc_name, :string, null: false
      add :oc_position, :string, null: false
      add :cpr, :integer, null: false
      add :updated_at, :utc_datetime_usec, null: false
    end

    create_if_not_exists unique_index(:organized_crime_cpr, [:user_id, :oc_name, :oc_position])
  end
end
