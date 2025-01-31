defmodule Tornium.Repo.Migrations.AddUserFactionPositionReference do
  use Ecto.Migration

  def up do
    # Will cause a duplicate_object constraint error without dropping the constraint
    # See https://github.com/elixir-ecto/ecto/issues/722
    drop_if_exists constraint("user", "user_faction_position_id_fkey")

    alter table("user") do
      add_if_not_exists :faction_position_id, references(:faction_position, column: :pid, type: :binary_id)
    end
  end

  def down do
    drop_if_exists constraint("user", "user_faction_position_id_fkey")

    alter table("user") do
      Ecto.Migration.remove_if_exists(:faction_position_id, references(:faction_position, column: :pid, type: :binary_id))
    end
  end
end
