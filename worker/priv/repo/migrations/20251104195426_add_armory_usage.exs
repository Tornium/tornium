defmodule Tornium.Repo.Migrations.AddArmoryUsage do
  use Ecto.Migration

  def change do
    create_if_not_exists table("armory_usage", primary_key: false) do
      add :timestamp, :utc_datetime, null: false
      add :id, :string, primary_key: true, autogenerate: false
      add :action, :string, null: false

      add :user_id, references(:user, column: :tid, type: :integer), null: false
      add :faction_id, references(:faction, column: :tid, type: :integer), null: false

      add :item_id, references(:item, column: :tid, type: :integer), null: false
      add :is_energy_refill, :boolean, default: false, null: false
      add :is_nerve_refill, :boolean, default: false, null: false

      add :quantity, :integer, null: false
    end
  end
end
