defmodule Tornium.Repo.Migrations.AddOcTeamRoles do
  use Ecto.Migration

  def change do
    alter table("server_oc_config") do
      add :team_roles, {:array, :bigint}, default: [], null: false
      add :team_features, {:array, :string}, default: [], null: false
    end
  end
end
