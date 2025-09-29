defmodule Tornium.Repo.Migrations.RenameOcNew do
  use Ecto.Migration

  def change do
    rename table("organized_crime_new"), to: table("organized_crime")
  end
end
