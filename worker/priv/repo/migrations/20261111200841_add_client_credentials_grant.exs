defmodule Tornium.Repo.Migrations.AddClientCredentialsGrant do
  use Ecto.Migration

  def change do
    create_if_not_exists table("oauth_client_resource_consent") do
      add :guid, :binary_id, primary_key: true

      add :client_id, references(:oauthclient, column: :client_id, type: :string), null: false
      add :scope, :text, default: "", null: false

      add :faction_id, references(:faction, column: :tid, type: :integer), default: nil, null: true
      add :server_id, references(:server, column: :sid, type: :bigint), default: nil, null: true

      add :consented_by_id, references(:user, column: :tid, type: :integer), null: false
      add :consented_at, :datetime_utc, null: false
      add :revoked_by_id, references(:user, column: :tid, type: :integer), default: nil, null: true
      add :revoked_at, :datetime_utc, default: nil, null: true
    end
    # There must be EXACTLY one resource for an appliction's consent.
    create constraint("oauth_client_resource_conent", :exactly_one_resource, check: "num_nonnulls(faction_id, server_id) = 1")
    # There must only be one active consent by a resource for a client.
    create unique_index("oauth_client_resource_conent", [:client_id, :faction_id], where: "faction_id IS NOT NULL AND revoked_at IS NULL")
    create unique_index("oauth_client_resource_conent", [:client_id, :server_id], where: "server_id IS NOT NULL AND revoked_at IS NULL")

    alter table("oauthtoken") do
      add :consent_id, references(:oauth_client_resource_consent, column: :guid, type: :binary_id), default: nil, null: true
    end
  end
end
