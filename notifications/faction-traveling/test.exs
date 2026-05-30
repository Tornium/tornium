defmodule Tornium.Notification.FactionSelfHosp.Test do
  use Tornium.NotificationInator.CaseTemplate
  import Tornium.NotificationInator.ListAssertions

  test "members not included after leaving faction", %{vm: base_vm, notification: notification} do
    vm =
      base_vm
      |> Lua.set!(["faction"], %{
        "name" => "Test",
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
          },
          "1" => %{
            "name" => "Chedburn",
            "status" => %{
              "description" => "Traveling from Torn to United Kingdom",
              "details" => nil,
              "state" => "Traveling",
              "color" => "blue",
              "until" => nil
            }
          }
        }
      })
      # Parameters
      |> Lua.set!(["TRAVEL_METHOD"], 2)
      # Internal notification data
      |> Lua.set!(["state"], %{})

    assert {[true, _render_state, passthrough_state], _vm} = Lua.eval!(vm, notification.code)

    vm =
      base_vm
      |> Lua.set!(["faction"], %{
        "name" => "Test",
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
      |> Lua.set!(["TRAVEL_METHOD"], 2)
      # Internal notification data
      |> Lua.set!(["state"], passthrough_state)

    assert {[true, render_state, passthrough_state], _vm} = Lua.eval!(vm, notification.code)

    assert_unordered(
      [
        {"abroad_members", []},
        {"faction_name", "Test"},
        {"flying_members", []},
        {"hospital_members", []},
        {"travel_method", "Airstrip"}
      ],
      render_state
    )

    assert_unordered([{"initialized", true}, {"members", []}], passthrough_state)
  end
end
