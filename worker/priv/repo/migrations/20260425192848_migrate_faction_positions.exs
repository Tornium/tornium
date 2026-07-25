defmodule Tornium.Repo.Migrations.MigrateFactionPositions do
  use Ecto.Migration

  def up do
    alter table("faction_position") do
      add :permissions, {:array, :string}, default: [], null: false
    end

    flush()

    execute """
    UPDATE faction_position
    SET permissions = array_remove(ARRAY[
      CASE WHEN use_medical_item THEN 'Medical Usage' END,
      CASE WHEN use_booster_item THEN 'Booster Usage' END,
      CASE WHEN use_drug_item THEN 'Drug Usage' END,
      CASE WHEN use_energy_refill THEN 'Energy Refill Usage' END,
      CASE WHEN use_nerve_refill THEN 'Nerve Refill Usage' END,
      CASE WHEN loan_temporary_item THEN 'Temporary Loaning' END,
      CASE WHEN loan_weapon_armory THEN 'Weapon & Armor Loaning' END,
      CASE WHEN retrieve_loaned_armory THEN 'Item Retrieving' END,
      CASE WHEN plan_init_oc THEN 'Organised Crimes' END,
      CASE WHEN access_fac_api THEN 'Faction API Access' END,
      CASE WHEN give_item THEN 'Item Giving' END,
      CASE WHEN give_money THEN 'Money Giving' END,
      CASE WHEN give_points THEN 'Points Giving' END,
      CASE WHEN manage_forums THEN 'Forum Management' END,
      CASE WHEN manage_applications THEN 'Application Management' END,
      CASE WHEN kick_members THEN 'Kick Members' END,
      CASE WHEN adjust_balances THEN 'Balance Adjustment' END,
      CASE WHEN manage_wars THEN 'War Management' END,
      CASE WHEN manage_upgrades THEN 'Upgrade Management' END,
      CASE WHEN send_newsletters THEN 'Newsletter Sending' END,
      CASE WHEN change_announcement THEN 'Announcement Changes' END,
      CASE WHEN change_description THEN 'Description Changes' END
    ], NULL)
    """

    alter table("faction_position") do
      remove :use_medical_item
      remove :use_booster_item
      remove :use_drug_item
      remove :use_energy_refill
      remove :use_nerve_refill
      remove :loan_temporary_item
      remove :loan_weapon_armory
      remove :retrieve_loaned_armory
      remove :plan_init_oc
      remove :access_fac_api
      remove :give_item
      remove :give_money
      remove :give_points
      remove :manage_forums
      remove :manage_applications
      remove :kick_members
      remove :adjust_balances
      remove :manage_wars
      remove :manage_upgrades
      remove :send_newsletters
      remove :change_announcement
      remove :change_description
    end
  end

  def down do
    alter table("faction_position") do
      add :use_medical_item, :boolean, default: false, null: false
      add :use_booster_item, :boolean, default: false, null: false
      add :use_drug_item, :boolean, default: false, null: false
      add :use_energy_refill, :boolean, default: false, null: false
      add :use_nerve_refill, :boolean, default: false, null: false
      add :loan_temporary_item, :boolean, default: false, null: false
      add :loan_weapon_armory, :boolean, default: false, null: false
      add :retrieve_loaned_armory, :boolean, default: false, null: false
      add :plan_init_oc, :boolean, default: false, null: false
      add :access_fac_api, :boolean, default: false, null: false
      add :give_item, :boolean, default: false, null: false
      add :give_money, :boolean, default: false, null: false
      add :give_points, :boolean, default: false, null: false
      add :manage_forums, :boolean, default: false, null: false
      add :manage_applications, :boolean, default: false, null: false
      add :kick_members, :boolean, default: false, null: false
      add :adjust_balances, :boolean, default: false, null: false
      add :manage_wars, :boolean, default: false, null: false
      add :manage_upgrades, :boolean, default: false, null: false
      add :send_newsletters, :boolean, default: false, null: false
      add :change_announcement, :boolean, default: false, null: false
      add :change_description, :boolean, default: false, null: false
    end

    flush()

    execute """
    UPDATE faction_position
    SET 
      use_medical_item = 'Medical Usage' = ANY(permissions),
      use_booster_item = 'Booster Usage' = ANY(permissions),
      use_drug_item = 'Drug Usage' = ANY(permissions),
      use_energy_refill = 'Energy Refill Usage' = ANY(permissions),
      use_nerve_refill = 'Nerve Refill Usage' = ANY(permissions),
      loan_temporary_item = 'Temporary Loaning' = ANY(permissions),
      loan_weapon_armory = 'Weapon & Armor Loaning' = ANY(permissions),
      retrieve_loaned_armory = 'Item Retrieving' = ANY(permissions),
      plan_init_oc = 'Organised Crimes' = ANY(permissions),
      access_fac_api = 'Faction API Access' = ANY(permissions),
      give_item = 'Item Giving' = ANY(permissions),
      give_money = 'Money Giving' = ANY(permissions),
      give_points = 'Points Giving' = ANY(permissions),
      manage_forums = 'Forum Management' = ANY(permissions),
      manage_applications = 'Application Management' = ANY(permissions),
      kick_members = 'Kick Members' = ANY(permissions),
      adjust_balances = 'Balance Adjustment' = ANY(permissions),
      manage_wars = 'War Management' = ANY(permissions),
      manage_upgrades = 'Upgrade Management' = ANY(permissions),
      send_newsletters = 'Newsletter Sending' = ANY(permissions),
      change_announcement = 'Announcement Changes' = ANY(permissions),
      change_description = 'Description Changes' = ANY(permissions)
    """

    alter table("faction_position") do
      remove :permissions
    end
  end
end
