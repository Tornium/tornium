defmodule Tornium.Repo.Migrations.RemoveOdChannelData do
  use Ecto.Migration

  def change do
    alter table("faction") do
      remove :od_channel, :integer
      remove :od_data, :map
    end
  end
end
