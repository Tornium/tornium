defmodule Tornium.Notification.FactionInactivity.Test do
  use Tornium.NotificationInator.CaseTemplate
  import Tornium.NotificationInator.ListAssertions

  @days 2
  @now DateTime.utc_now()
  @one_day_ago @now |> DateTime.add(-1, :day) |> DateTime.to_unix()
  @two_days_ago @now |> DateTime.add(-2, :day) |> DateTime.to_unix()

  test "no inactive members", %{vm: vm, notification: notification} do
    vm =
      vm
      # API data
      |> Lua.set!(["faction"], %{
        "name" => "Test",
        "ranked_wars" => %{},
        "members" => %{
          "2383326" => %{
            "name" => "tiksan",
            "last_action" => %{
              "status" => "Online",
              "timestamp" => @now |> DateTime.to_unix(),
              "relative" => "1 minute ago"
            },
            "status" => %{
              "description" => "Okay",
              "details" => "",
              "state" => "Okay",
              "color" => "green",
              "until" => 0
            }
          }
        }
      })
      # Parameters
      |> Lua.set!(["DAYS"], @days)
      # Internal notification data
      |> Lua.set!(["state"], %{})

    assert {[false, render_state, _passthrough_state], _vm} = Lua.eval!(vm, notification.code)

    assert_unordered(
      [{"configured_days", 2}, {"inactive_members", []}, {"faction_name", "Test"}],
      render_state
    )
  end

  test "inactive member below configured number", %{vm: vm, notification: notification} do
    vm =
      vm
      # API data
      |> Lua.set!(["faction"], %{
        "name" => "Test",
        "ranked_wars" => %{},
        "members" => %{
          "2383326" => %{
            "name" => "tiksan",
            "last_action" => %{
              "status" => "Offline",
              "timestamp" => @one_day_ago,
              "relative" => "1 day ago"
            },
            "status" => %{
              "description" => "Okay",
              "details" => "",
              "state" => "Okay",
              "color" => "green",
              "until" => 0
            }
          }
        }
      })
      # Parameters
      |> Lua.set!(["DAYS"], @days)
      # Internal notification data
      |> Lua.set!(["state"], %{})

    assert {[false, render_state, _passthrough_state], _vm} = Lua.eval!(vm, notification.code)

    assert_unordered(
      [{"configured_days", 2}, {"inactive_members", []}, {"faction_name", "Test"}],
      render_state
    )
  end

  test "inactive member", %{vm: vm, notification: notification} do
    vm =
      vm
      # API data
      |> Lua.set!(["faction"], %{
        "name" => "Test",
        "ranked_wars" => %{},
        "members" => %{
          "2383326" => %{
            "name" => "tiksan",
            "last_action" => %{
              "status" => "Offline",
              "timestamp" => @two_days_ago,
              "relative" => "2 days ago"
            },
            "status" => %{
              "description" => "Okay",
              "details" => "",
              "state" => "Okay",
              "color" => "green",
              "until" => 0
            }
          }
        }
      })
      # Parameters
      |> Lua.set!(["DAYS"], @days)
      # Internal notification data
      |> Lua.set!(["state"], %{})

    assert {[true, render_state, _passthrough_state], _vm} = Lua.eval!(vm, notification.code)

    assert_unordered(
      [
        {"configured_days", 2},
        {"inactive_members", [{1, _inactive_member}]},
        {"faction_name", "Test"}
      ],
      render_state
    )

    {"inactive_members", [{1, inactive_member}]} = List.keyfind(render_state, "inactive_members", 0)

    assert_unordered(
      [
        {"id", "2383326"},
        {"fedded", false},
        {"fedded_reason", "Okay"},
        {"recruit", false},
        {"username", "tiksan [2383326]"},
        {"last_action", @two_days_ago}
      ],
      inactive_member
    )

    generate_message(render_state)
  end

  test "inactive fedded member", %{vm: vm, notification: notification} do
    vm =
      vm
      # API data
      |> Lua.set!(["faction"], %{
        "name" => "Test",
        "ranked_wars" => %{},
        "members" => %{
          "2383326" => %{
            "name" => "tiksan",
            "last_action" => %{
              "status" => "Offline",
              "timestamp" => @two_days_ago,
              "relative" => "2 days ago"
            },
            "status" => %{
              "description" => "In federal jail for 6 days",
              "details" => "Multiple accounts",
              "state" => "Federal",
              "color" => "red",
              "until" => @now |> DateTime.add(6, :day) |> DateTime.to_unix()
            }
          }
        }
      })
      # Parameters
      |> Lua.set!(["DAYS"], @days)
      # Internal notification data
      |> Lua.set!(["state"], %{})

    assert {[true, render_state, _passthrough_state], _vm} = Lua.eval!(vm, notification.code)

    assert_unordered(
      [
        {"configured_days", 2},
        {"inactive_members", [{1, _inactive_member}]},
        {"faction_name", "Test"}
      ],
      render_state
    )

    {"inactive_members", [{1, inactive_member}]} = List.keyfind(render_state, "inactive_members", 0)

    assert_unordered(
      [
        {"id", "2383326"},
        {"fedded", true},
        {"fedded_reason", "In federal jail for 6 days"},
        {"recruit", false},
        {"username", "tiksan [2383326]"},
        {"last_action", @two_days_ago}
      ],
      inactive_member
    )

    generate_message(render_state)
  end
end
