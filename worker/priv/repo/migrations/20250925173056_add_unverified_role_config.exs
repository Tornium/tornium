defmodule Tornium.Repo.Migrations.AddUnverifiedRoleConfig do
  use Ecto.Migration

  def change do
    alter table("server") do
      add :unverified_roles, {:array, :bigint}, default: [], null: false
    end
  end
end
