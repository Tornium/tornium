defmodule Tornium.Repo.Migrations.AddFactionPosition do
  use Ecto.Migration

  def up do
    create_if_not_exists table("faction_position", primary_key: false) do
      add :pid, :binary_id, primary_key: true
      add :name, :string, null: false
      add :faction_tid, :integer, null: false

      add :default, :boolean, default: false, null: false

      add :use_medical_item, :boolean, null: false
      add :use_booster_item, :boolean, null: false
      add :use_drug_item, :boolean, null: false
      add :use_energy_refill, :boolean, null: false
      add :use_nerve_refill, :boolean, null: false
      add :loan_temporary_item, :boolean, null: false
      add :loan_weapon_armory, :boolean, null: false
      add :retrieve_loaned_armory, :boolean, null: false
      add :plan_init_oc, :boolean, null: false
      add :access_fac_api, :boolean, null: false
      add :give_item, :boolean, null: false
      add :give_money, :boolean, null: false
      add :give_points, :boolean, null: false
      add :manage_forums, :boolean, null: false
      add :manage_applications, :boolean, null: false
      add :kick_members, :boolean, null: false
      add :adjust_balances, :boolean, null: false
      add :manage_wars, :boolean, null: false
      add :manage_upgrades, :boolean, null: false
      add :send_newsletters, :boolean, null: false
      add :change_announcement, :boolean, null: false
      add :change_description, :boolean, null: false
    end
    create unique_index(:faction_position, [:pid])
  end

  def down do
    drop table("faction")
  end
end
