defmodule Tornium.Repo.Migrations.AddMissingMemberOc do
  use Ecto.Migration

  def change do
    alter table("server_oc_config") do
      add :missing_member_channel, :bigint, default: nil, null: true
      add :missing_member_roles, {:array, :bigint}, default: [], null: false
      add :missing_member_minimum_duration, :interval, default: fragment("'1 day'::interval"), null: false
    end
  end
end
