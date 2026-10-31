defmodule Tornium.ObanRepo.Migrations.ChangeObanJobsUnlogged do
  use Ecto.Migration

  def change do
    execute("ALTER TABLE oban_jobs SET UNLOGGED;", "ALTER TABLE oban_jobs SET LOGGED;")
  end
end
