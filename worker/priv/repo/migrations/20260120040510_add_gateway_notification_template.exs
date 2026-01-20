defmodule Tornium.Repo.Migrations.AddGatewayNotificationTemplate do
  use Ecto.Migration

  def up do
    alter table("notification_trigger") do
      add :gateway_template, :text, null: true
      modify :message_template, :text, null: true
    end

    execute("""
    ALTER TABLE notification_trigger
    ADD CONSTRAINT notification_trigger_template_constraint
    CHECK (num_nonnulls(message_template, gateway_template) >= 1)
    """)
  end
  
  def down do
    execute("""
    ALTER TABLE notification_trigger
    DROP CONSTRAINT IF EXISTS notification_trigger_template_constraint
    """)

    alter table("notification_trigger") do
      remove :gateway_template
      modify :message_template, :text, null: false
    end
  end
end
