defmodule Tornium.Repo.Migrations.AddUserFeddedUntil do
  use Ecto.Migration

  def change do
    alter table("user") do
      add :fedded_until, :date, default: nil, null: true
    end
  end
end
