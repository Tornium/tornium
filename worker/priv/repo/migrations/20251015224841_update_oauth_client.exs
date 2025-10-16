defmodule Tornium.Repo.Migrations.UpdateOauthClient do
  use Ecto.Migration

  def change do
    alter table("oauthclient") do
      modify :client_secret, :string, default: nil, null: true
      add :deleted_at, :utc_datetime, default: nil, null: true
    end
  end
end
