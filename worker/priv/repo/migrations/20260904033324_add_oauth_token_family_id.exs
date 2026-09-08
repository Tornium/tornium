defmodule Tornium.Repo.Migrations.AddOauthTokenFamilyId do
  use Ecto.Migration

  def change do
    alter table("oauthtoken") do
      add :family_id, :binary_id, default: fragment("gen_random_uuid()"), null: false
      add :refresh_token_expires_in, :bigint, default: nil, null: true
    end
  end
end
