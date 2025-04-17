defmodule Tornium.Repo.Migrations.AddExtraRangeSentFlags do
  use Ecto.Migration

  def change do
    alter table("organized_crime_slot") do
      add :sent_extra_range_notification, :boolean, default: false, null: false
    end
  end
end
