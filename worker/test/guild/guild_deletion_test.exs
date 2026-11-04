# Copyright (C) 2021-2025 tiksan
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

defmodule Tornium.Test.Guild.Delete do
  use Tornium.RepoCase

  test "test deleting no servers" do
    assert_raise(FunctionClauseError, fn -> Tornium.Schema.Server.delete_servers([]) end)
  end

  test "test deleting correct server" do
    Tornium.Schema.Server.new(1, "1")
    Tornium.Schema.Server.new(2, "2")

    {count, _} = Tornium.Schema.Server.delete_servers([1])
    assert count == 1

    assert not (Tornium.Schema.Server |> where([s], s.sid == 1) |> Repo.exists?())
    assert Tornium.Schema.Server |> where([s], s.sid == 2) |> Repo.exists?()
  end

  test "test deleting server with linked faction" do
    Repo.insert(%Tornium.Schema.Server{sid: 1, name: "1", factions: [1]})
    Repo.insert(%Tornium.Schema.Server{sid: 2, name: "1", factions: [3]})

    Repo.insert(%Tornium.Schema.Faction{tid: 1, name: "1", guild_id: 1})
    Repo.insert(%Tornium.Schema.Faction{tid: 2, name: "2", guild_id: 1})
    Repo.insert(%Tornium.Schema.Faction{tid: 3, name: "2", guild_id: 2})

    Tornium.Schema.Server.delete_servers([1])

    faction_one = Repo.get(Tornium.Schema.Faction, 1)
    faction_two = Repo.get(Tornium.Schema.Faction, 2)
    faction_three = Repo.get(Tornium.Schema.Faction, 3)

    assert not is_nil(faction_one)
    assert not is_nil(faction_two)
    assert not is_nil(faction_three)

    assert is_nil(faction_one.guild_id)
    assert is_nil(faction_two.guild_id)
    assert not is_nil(faction_three.guild_id)
  end

  test "test deleting attack notifications" do
    Tornium.Schema.Server.new(1, "1")
  end

  # TODO: delete notification config

  # TODO: delete oc range config

  test "test deleting notifications with an assigned server" do
    Tornium.Schema.Server.new(1, "1")

    trigger_id = Ecto.UUID.generate()
    deletion_notification_id = Ecto.UUID.generate()
    other_notification_id = Ecto.UUID.generate()

    Repo.insert(%Tornium.Schema.User{tid: 1, name: "1"})

    Repo.insert(%Tornium.Schema.Trigger{
      tid: trigger_id,
      name: "test",
      description: "test",
      owner_id: 1,
      cron: "",
      next_execution: DateTime.utc_now() |> DateTime.truncate(:second),
      resource: :user,
      selections: [],
      code: "",
      parameters: %{},
      message_type: :send,
      message_template: "",
      restricted_data: false,
      official: false
    })

    Repo.insert(%Tornium.Schema.Notification{
      nid: deletion_notification_id,
      trigger_id: trigger_id,
      server_id: 1,
      user_id: 1
    })

    Repo.insert(%Tornium.Schema.Notification{
      nid: other_notification_id,
      trigger_id: trigger_id,
      server_id: nil,
      user_id: 1
    })

    Tornium.Schema.Server.delete_servers([1])

    assert not (Tornium.Schema.Notification |> where([n], n.nid == ^deletion_notification_id) |> Repo.exists?())
    assert Tornium.Schema.Notification |> where([n], n.nid == ^other_notification_id) |> Repo.exists?()
    assert Tornium.Schema.Trigger |> where([t], t.tid == ^trigger_id) |> Repo.exists?()
  end
end
