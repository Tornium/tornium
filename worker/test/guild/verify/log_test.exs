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

defmodule Tornium.Test.Guild.Verify.Log do
  use Tornium.RepoCase, async: false
  alias Tornium.Schema.VerificationLog

  setup do
    user_one = %Tornium.Schema.User{tid: 1, name: "Chedburn", discord_id: 1} |> Repo.insert!()
    server = %Tornium.Schema.Server{sid: 1, name: "Test server"} |> Repo.insert!()

    {:ok, user_one: user_one, server: server}
  end

  describe "database logs insertion" do
    test "insert nothing" do
      assert {0, nil} = VerificationLog.insert_all([])
    end

    test "insert single log", %{user_one: user_one, server: server} do
      assert {1, nil} =
               VerificationLog.insert_all([
                 %VerificationLog{
                   server_id: server.sid,
                   discord_id: user_one.discord_id,
                   user_id: user_one.tid,
                   new_nickname: "new",
                   old_nickname: "old",
                   roles_removed: [1, 2, 3],
                   roles_added: [4, 5, 6],
                   timestamp: DateTime.utc_now() |> DateTime.truncate(:second)
                 }
               ])

      log =
        Tornium.Schema.VerificationLog
        |> where([l], l.user_id == ^user_one.tid)
        |> Repo.one!()

      assert log.server_id == server.sid
      assert log.discord_id == user_one.discord_id
      assert log.user_id == user_one.tid
      assert log.new_nickname == "new"
      assert log.old_nickname == "old"
      assert log.roles_removed == [1, 2, 3]
      assert log.roles_added == [4, 5, 6]
    end

    test "insert multiple logs" do
      # TODO: Add this
    end
  end
end
