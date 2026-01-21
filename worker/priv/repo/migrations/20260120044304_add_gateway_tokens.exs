defmodule Tornium.Repo.Migrations.AddGatewayTokens do
  use Ecto.Migration

  def change do
    create_if_not_exists table("gateway_token", primary_key: false) do
      add :guid, :binary, primary_key: true, autogenerate: true
      add :user_id, references(:user, column: :tid, type: :integer), null: false

      add :created_at, :utc_datetime, null: false, default: fragment("now()")
      add :created_ip, :inet, null: false
      add :expires_at, :utc_datetime, null: false
    end

    create index(:gateway_token, :user_id)
  end
end
