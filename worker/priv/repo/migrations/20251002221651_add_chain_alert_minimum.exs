defmodule Tornium.Repo.Migrations.AddChainAlertMinimum do
  use Ecto.Migration

  def change do
    alter table("serverattackconfig") do
      add :chain_alert_minimum, :integer, default: 60, null: false
    end
  end
end
