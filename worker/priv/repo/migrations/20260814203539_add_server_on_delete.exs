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
        from: references(:server, column: :sid, type: :bigint), null: true
      )
    end

    alter table("server_oc_config") do
      modify(
        :server_id,
        references(:server, column: :sid, type: :bigint, on_delete: :delete_all),
        from: references(:server, column: :sid, type: :bigint), null: false
      )
    end

    alter table("server_oc_range_config") do
      modify(
        :server_oc_config_id,
        references(:server_oc_config, column: :guid, type: :binary_id, on_delete: :delete_all),
        from: references(:server_oc_config, column: :guid, type: :binary_id), null: false
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
  end
end
