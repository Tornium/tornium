defmodule Tornium.Repo.Migrations.AddNullableUserName do
  use Ecto.Migration

  def up do
    alter table("user") do
      modify :name, :string, size: 15, null: true, default: nil
    end
  end

  def down do
    alter table("user") do
      modify :name, :string, size: 15, null: false, default: ""
    end
  end
end
