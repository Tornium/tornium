defmodule Tornium.Repo.Migrations.AddClientCredentialsGrant do
  use Ecto.Migration

  def change do
    create_if_not_exists table("oauth_client_resource_consent", primary_key: false) do
      add :guid, :binary_id, primary_key: true, default: fragment("gen_random_uuid()")

      add :client_id, references(:oauthclient, column: :client_id, type: :string), null: false
      add :scope, :text, default: "", null: false

      add :faction_id, references(:faction, column: :tid, type: :integer), default: nil, null: true
      add :server_id, references(:server, column: :sid, type: :bigint), default: nil, null: true, on_delete: :delete_all
      # We can delete this as we should have logs for this elsewhere (eventually).

      add :consented_by_id, references(:user, column: :tid, type: :integer), null: false
      add :consented_at, :utc_datetime_usec, null: false
      add :revoked_by_id, references(:user, column: :tid, type: :integer), default: nil, null: true
      add :revoked_at, :utc_datetime_usec, default: nil, null: true
    end
    # There must be EXACTLY one resource for an appliction's consent.
    create constraint("oauth_client_resource_consent", :exactly_one_resource, check: "num_nonnulls(faction_id, server_id) = 1")
    # There must only be one active consent by a resource for a client.
    create unique_index("oauth_client_resource_consent", [:client_id, :faction_id], where: "faction_id IS NOT NULL AND revoked_at IS NULL")
    create unique_index("oauth_client_resource_consent", [:client_id, :server_id], where: "server_id IS NOT NULL AND revoked_at IS NULL")

    alter table("oauthtoken") do
      add :consent_id, references(:oauth_client_resource_consent, column: :guid, type: :binary_id), default: nil, null: true
    end
    # The oauth token should only require a user ID when the client of the token is
    # not of client credentials grant as it wouldn't have a user ID.
    execute "ALTER TABLE oauthtoken ALTER COLUMN user_id DROP NOT NULL", "ALTER TABLE oauthtoken ALTER COLUMN user_id SET NOT NULL"
  end
end
