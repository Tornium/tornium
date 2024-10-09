defmodule Tornium.Repo.Migrations.AddUserFactionReference do
  use Ecto.Migration

  def up do
    # Will cause a duplicate_object constraint error without dropping the constraint
    # See https://github.com/elixir-ecto/ecto/issues/722
    drop constraint("user", "user_faction_id_fkey")

    alter table("user") do
      add_if_not_exists :faction_id, references(:faction, column: :tid, type: :integer)
    end
  end

  def down do
    drop constraint("user", "user_faction_id_fkey")

    alter table("user") do
      Ecto.Migration.remove_if_exists(:faction_id)
    end
  end
end
