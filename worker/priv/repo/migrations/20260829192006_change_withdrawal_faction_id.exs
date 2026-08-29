defmodule Tornium.Repo.Migrations.ChangeWithdrawalFactionId do
  use Ecto.Migration

  def up do
    rename table("withdrawal"), :faction_tid, to: :faction_id
    rename table("withdrawal"), :requester, to: :requester_id

    alter table("withdrawal") do
      modify :faction_id, references(:faction, column: :tid, type: :integer), null: false
      modify :requester_id, references(:user, column: :tid, type: :integer), null: false
    end
  end

  def down do
    alter table("withdrawal") do
      modify :faction_id, :integer
      modify :requester_id, :integer
    end

    rename table("withdrawal"), :faction_id, to: :faction_tid
    rename table("withdrawal"), :requester_id, to: :requester
  end
end
