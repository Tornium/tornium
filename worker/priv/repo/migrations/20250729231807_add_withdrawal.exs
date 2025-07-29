defmodule Tornium.Repo.Migrations.AddWithdrawal do
  use Ecto.Migration

  def change do
    create_if_not_exists table("withdrawal", primary_key: false) do
      add :wid, :id, primary_key: true, autogenerate: true
      add :guid, :binary_id, null: false
      add :faction_tid, :integer, null: false
      add :amount, :bigint, null: false
      add :cash_request, :boolean, default: true, null: false
      add :requester, :integer, null: false
      add :time_requested, :utc_datetime, null: false
      add :status, :integer, default: 0, null: false
      add :fulfiller, :integer, default: nil, null: true
      add :time_fulfilled, :utc_datetime, default: nil, null: true
      add :withdrawal_message, :bigint, null: false
    end

    create_if_not_exists unique_index(:withdrawal, [:guid])
  end
end
