defmodule Tornium.Repo.Migrations.AddOauthTokenFamilyId do
  use Ecto.Migration

  def change do
    create_if_not_exists table("oauthtoken", primary_key: false) do
      add :id, :serial, primary_key: true

      add :client_id, references(:oauthclient, column: :client_id, type: :string), null: false
      add :token_type, :string, size: 40, null: false
      add :access_token, :string, size: 255, null: false
      add :refresh_token, :string, size: 255, default: nil, null: true
      add :scope, :text, null: false
      add :issued_at, :utc_datetime_usec, null: false
      add :access_token_revoked_at, :utc_datetime_usec, default: nil, null: true
      add :refresh_token_revoked_at, :utc_datetime_usec, default: nil, null: true
      add :expires_in, :bigint, null: false

      add :user_id, references(:user, column: :tid, type: :integer), null: false
    end

    create_if_not_exists unique_index(:oauthtoken, [:access_token])
    create_if_not_exists index(:oauthtoken, [:client_id])
    create_if_not_exists index(:oauthtoken, [:refresh_token])
    create_if_not_exists index(:oauthtoken, [:user_id])


    alter table("oauthtoken") do
      add :family_id, :binary_id, default: fragment("gen_random_uuid()"), null: false
      add :refresh_token_expires_in, :bigint, default: nil, null: true
    end
  end
end
