defmodule Tornium.Repo.Migrations.UpdateOauthClient do
  use Ecto.Migration

  def change do
    create_if_not_exists table("oauthclient") do
      add :client_id, :string, primary_key: true
      add :client_secret, :string, null: false
      add :client_id_issued_at, :utc_datetime, default: fragment("now()"), null: false
      add :client_secret_expires_at, :utc_datetime, default: nil, null: true
      add :client_metadata, :map, null: false
      add :user_id, references(:user, column: :tid, type: :integer), null: false
    end

    alter table("oauthclient") do
      modify :client_secret, :string, default: nil, null: true
      add :deleted_at, :utc_datetime, default: nil, null: true
    end
  end
end
