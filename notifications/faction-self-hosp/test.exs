defmodule Tornium.Notification.FactionSelfHosp.Test do
  use Tornium.NotificationInator.CaseTemplate
  import Tornium.NotificationInator.ListAssertions

  @minutes 5
  @yesterday DateTime.utc_now() |> DateTime.add(-1, :day) |> DateTime.to_unix()
  @soon DateTime.utc_now() |> DateTime.add(1, :minute) |> DateTime.to_unix()
  @tomorrow DateTime.utc_now() |> DateTime.add(1, :day) |> DateTime.to_unix()

  test "no hospitalized members and no RWs", %{vm: vm, notification: notification} do
    vm =
      vm
      # API data
      |> Lua.set!(["faction"], %{
        "name" => "Test",
        "ranked_wars" => %{},
        "members" => %{
          "2383326" => %{
            "name" => "tiksan",
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
      |> Lua.set!(["MINUTES"], @minutes)
      |> Lua.set!(["ONLY_RW"], "false")
      # Internal notification data
      |> Lua.set!(["state"], %{})

    assert {[false, render_state, _passthrough_state], _vm} = Lua.eval!(vm, notification.code)

    assert_unordered(
      [{"configured_minutes", 5}, {"members_leaving_hosp", []}, {"faction_name", "Test"}],
      render_state
    )
  end

  test "disabled with future RW", %{vm: vm, notification: notification} do
    vm =
      vm
      # API data
      |> Lua.set!(["faction"], %{
        "name" => "Test",
        "ranked_wars" => %{
          "1" => %{"war" => %{"start" => @tomorrow, "end" => 0, "target" => 99999, "winner" => 0}}
        },
        "members" => %{
          "2383326" => %{
            "name" => "tiksan",
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
      |> Lua.set!(["MINUTES"], @minutes)
      |> Lua.set!(["ONLY_RW"], "true")
      # Internal notification data
      |> Lua.set!(["state"], %{})

    assert {[false, [], _passthrough_state], _vm} = Lua.eval!(vm, notification.code)
  end

  test "only RW during RW", %{vm: vm, notification: notification} do
    vm =
      vm
      # API data
      |> Lua.set!(["faction"], %{
        "name" => "Test",
        "ranked_wars" => %{
          "1" => %{
            "war" => %{
              "start" => @yesterday,
              "end" => 0,
              "target" => 99999,
              "winner" => 0
            }
          }
        },
        "members" => %{
          "1" => %{
            "name" => "Chedburn",
            "status" => %{
              "description" => "In hospital for 1 mins ",
              "details" => "Hospitalized by <a href=\"https://torn.com\">Chedburn</a>",
              "state" => "Hospital",
              "color" => "red",
              "until" => @soon
            }
          },
          "2383326" => %{
            "name" => "tiksan",
            "status" => %{
              "description" => "In hospital for 3 hrs 37 mins ",
              "details" => "Hospitalized by <a href=\"https://torn.com\">Chedburn</a>",
              "state" => "Hospital",
              "color" => "red",
              "until" => @tomorrow
            }
          }
        }
      })
      # Parameters
      |> Lua.set!(["MINUTES"], @minutes)
      |> Lua.set!(["ONLY_RW"], "true")
      # Internal notification data
      |> Lua.set!(["state"], %{})

    assert {[true, render_state, _passthrough_state], _vm} = Lua.eval!(vm, notification.code)

    assert %{
             "configured_minutes" => 5,
             "members_leaving_hosp" => %{1 => %{"id" => 1}},
             "faction_name" => "Test"
           } = Tornium.Utils.tuples_to_map(render_state)
  end
end
