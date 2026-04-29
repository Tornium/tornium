defmodule Tornium.Repo.Migrations.AddPublicDataUsageToggle do
  use Ecto.Migration

  def change do
    alter table("user_settings") do
      add :public_data_enabled, :boolean, default: false, null: false
    end
  end
end
