defmodule Tornium.Repo.Migrations.AddElimination do
  use Ecto.Migration

  def change do
    create_if_not_exists table("elimination_team", primary_key: false) do
      add :guid, :binary_id, primary_key: true, autogenerate: true
      add :year, :integer, null: false
      add :name, :string, null: false
    end
    create_if_not_exists unique_index(:elimination_team, [:year, :name])

    create_if_not_exists table("elimination_member", primary_key: false) do
      add :guid, :binary_id, primary_key: true, autogenerate: true
      add :user_id, references(:user, column: :tid, type: :integer), null: false
      add :team_id, references(:elimination_team, column: :guid, type: :binary_id), null: false
    end
    create_if_not_exists unique_index(:elimination_member, [:user_id, :team_id])

    create_if_not_exists table("elimination_record", primary_key: false) do
      add :guid, :binary_id, primary_key: true, autogenerate: true
      add :member_id, references(:elimination_member, column: :guid, type: :binary_id), null: false
      add :timestamp, :utc_datetime, null: false

      add :score, :integer, default: 0, null: false
      add :attacks, :integer, default: 0, null: false
    end
    create_if_not_exists unique_index(:elimination_record, [:member_id, :timestamp])

    create_if_not_exists table("server_verification_elimination_config", primary_key: false) do
      add :guid, :binary_id, primary_key: true, autogenerate: true
      add :server_id, references(:server, column: :sid, type: :bigint), null: false
      add :team_id, references(:elimination_team, column: :guid, type: :binary_id), null: false

      add :roles, {:array, :bigint}, default: [], null: false
    end
    create_if_not_exists unique_index(:server_verification_elimination_config, [:server_id, :team_id])
  end
end
