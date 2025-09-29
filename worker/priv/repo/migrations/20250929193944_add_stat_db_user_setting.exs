defmodule Tornium.Repo.Migrations.AddStatDbUserSetting do
  use Ecto.Migration

  def change do
    alter table("user_settings") do
      add :stat_db_enabled, :boolean, default: true, null: false
    end
  end
end
