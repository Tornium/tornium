defmodule Tornium.Repo.Migrations.AddServerOnDelete do
  use Ecto.Migration

  def change do
    alter table("server_notifications_config") do
      modify(
        :server_id,
        references(:server, column: :sid, type: :bigint, on_delete: :delete_all),
        from: references(:server, column: :sid, type: :bigint), null: false
      )
    end

    alter table("notification") do
      modify(
        :server_id,
        references(:server, column: :sid, type: :bigint, on_delete: :delete_all),
        from: references(:server, column: :sid, type: :bigint), null: false
      )
    end

    alter table("server_oc_config") do
      modify(
        :server_id,
        references(:server, column: :sid, type: :bigint, on_delete: :delete_all),
        from: references(:server, column: :sid, type: :bigint), null: false
      )
    end

    alter table("server_overdose_config") do
      modify(
        :server_id,
        references(:server, column: :sid, type: :bigint, on_delete: :delete_all),
        from: references(:server, column: :sid, type: :bigint), null: false
      )
    end

    alter table("serverattackconfig") do
      modify(
        :server_id,
        references(:server, column: :sid, type: :bigint, on_delete: :delete_all),
        from: references(:server, column: :sid, type: :bigint), null: false
      )
    end

    alter table("verification_log") do
      modify(
        :server_id,
        references(:server, column: :sid, type: :bigint, on_delete: :delete_all),
        from: references(:server, column: :sid, type: :bigint), null: false
      )
    end
  end
end
