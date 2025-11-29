defmodule Tornium.Repo.Migrations.FixArmoryUsageOdEvents do
  use Ecto.Migration

  def up do
    alter table("armory_usage") do
      add :recipient_id, references(:user, column: :tid, type: :integer), null: false
    end

    alter table("overdose_event") do
      remove_if_exists :drug
      add :drug_id, references(:item, column: :tid, type: :integer), null: true
    end
  end

  def down do
    alter table("armory_usage") do
      remove_if_exists :recipient_id
    end

    alter table("overdose_event") do
      remove_if_exists :drug
      add :drug, :string, default: nil, null: true
    end
  end
end
