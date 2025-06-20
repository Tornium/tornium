defmodule Tornium.Repo.Migrations.AddOcTeamConfig do
  use Ecto.Migration

  def change do
    alter table("server_oc_config") do
      add :team_channel, :bigint, default: nil, null: true
    end
  end
end
