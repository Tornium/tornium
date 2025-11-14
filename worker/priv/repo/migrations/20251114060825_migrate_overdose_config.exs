defmodule Tornium.Repo.Migrations.MigrateOverdoseConfig do
  use Ecto.Migration

  import Ecto.Query

  def up do
    Tornium.Schema.Faction
    |> Tornium.Repo.all()
    |> Enum.each(fn
      %Tornium.Schema.Faction{
        tid: faction_id,
        od_channel: faction_od_channel,
        guild_id: faction_guild_id
      } when is_integer(faction_od_channel) and faction_od_channel != 0 and is_integer(faction_guild_id) and faction_guild_id != 0 -> 
        %Tornium.Schema.ServerOverdoseConfig{
          guid: Ecto.UUID.generate(),
          server_id: faction_guild_id,
          faction_id: faction_id,
          channel: faction_od_channel
        }
        |> Tornium.Repo.insert(on_conflict: :nothing, conflict_target: [:server_id, :faction_id])

      _ -> nil
    end)
  end

  def down do
  end
end
