defmodule Tornium.Repo.Migrations.WithdrawalExpiresAt do
  use Ecto.Migration
  import Ecto.Query
  alias Tornium.Repo

  def up do
    alter table("withdrawal") do
      add :expires_at, :utc_datetime, null: true
    end

    flush()

    Tornium.Schema.Withdrawal
    |> update([w], set: [expires_at: datetime_add(w.time_requested, 1, "hour")])
    |> Repo.update_all([])
  end

  def down do
    alter table("withdrawal") do
      remove :expires_at
    end
  end
end
