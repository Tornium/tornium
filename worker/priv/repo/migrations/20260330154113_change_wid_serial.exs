defmodule Tornium.Repo.Migrations.ChangeWidSerial do
  use Ecto.Migration

  def up do
    execute "CREATE SEQUENCE withdrawal_wid_seq OWNED BY withdrawal.wid"
    execute "ALTER TABLE withdrawal ALTER COLUMN wid SET DEFAULT nextval('withdrawal_wid_seq')"
    execute "SELECT setval('withdrawal_wid_seq', COALESCE((SELECT MAX(wid) FROM withdrawal), 1), true)"
  end

  def down do
    execute "ALTER TABLE withdrawal ALTER COLUMN wid DROP DEFAULT"
    execute "DROP SEQUENCE IF EXISTS withdrawal_wid_seq"
  end
end
