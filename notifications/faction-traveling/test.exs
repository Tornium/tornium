defmodule Tornium.Notification.FactionSelfHosp.Test do
  use Tornium.NotificationInator.CaseTemplate
  import Tornium.NotificationInator.ListAssertions

  test "member traveling somewhere", %{vm: base_vm, notification: notification} do
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
              "details" => "",
              "state" => "Traveling",
              "color" => "blue",
              "until" => 0
            }
          }
        }
      })
      # Parameters
      |> Lua.set!(["TRAVEL_METHOD"], 2)
      # Internal notification data
      |> Lua.set!(["state"], %{initialized: true})

    assert {[true, render_state, passthrough_state], _vm} = Lua.eval!(vm, notification.code)

    assert %{
             "initialized" => initialized,
             "members" => members
           } =
             Tornium.Utils.tuples_to_map(passthrough_state)

    assert true = initialized

    assert %{
             "United Kingdom" => %{
               "1" => %{"landed" => false, "name" => "Chedburn", "tid" => "1"}
             }
           } = members

    assert %{
             "abroad_members" => abroad_members,
             "faction_name" => "Test",
             "flying_members" => flying_members,
             "hospital_members" => hospital_members,
             "travel_method" => "Airstrip"
           } = Tornium.Utils.tuples_to_map(render_state)

    assert %{} = abroad_members
    assert %{} = hospital_members
    assert %{"United Kingdom" => %{"1" => %{"tid" => "1"}}} = flying_members

    generate_message(render_state)
  end

  test "member traveling back to Torn", %{vm: base_vm, notification: notification} do
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
              "description" => "Traveling from South Africa to Torn",
              "details" => "",
              "state" => "Traveling",
              "color" => "blue",
              "until" => 0
            }
          }
        }
      })
      # Parameters
      |> Lua.set!(["TRAVEL_METHOD"], 2)
      # Internal notification data
      |> Lua.set!(["state"], %{initialized: true})

    assert {[true, render_state, passthrough_state], _vm} = Lua.eval!(vm, notification.code)

    assert %{
             "initialized" => initialized,
             "members" => members
           } =
             Tornium.Utils.tuples_to_map(passthrough_state)

    assert true = initialized

    assert %{
             "Torn" => %{
               "1" => %{"landed" => false, "name" => "Chedburn", "tid" => "1"}
             }
           } = members

    assert %{
             "abroad_members" => abroad_members,
             "faction_name" => "Test",
             "flying_members" => flying_members,
             "hospital_members" => hospital_members,
             "travel_method" => "Airstrip"
           } = Tornium.Utils.tuples_to_map(render_state)

    assert %{} = abroad_members
    assert %{} = hospital_members
    assert %{"Torn" => %{"1" => %{"tid" => "1"}}} = flying_members

    generate_message(render_state)
  end

  test "member abroad", %{vm: base_vm, notification: notification} do
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
              "description" => "In Hawaii",
              "details" => "",
              "state" => "Abroad",
              "color" => "blue",
              "until" => 0
            }
          }
        }
      })
      # Parameters
      |> Lua.set!(["TRAVEL_METHOD"], 2)
      # Internal notification data
      |> Lua.set!(["state"], %{initialized: true})

    assert {[true, render_state, passthrough_state], _vm} = Lua.eval!(vm, notification.code)

    assert %{
             "initialized" => initialized,
             "members" => members
           } =
             Tornium.Utils.tuples_to_map(passthrough_state)

    assert true = initialized

    assert %{
             "Hawaii" => %{
               "1" => %{"landed" => true, "name" => "Chedburn", "tid" => "1"}
             }
           } = members

    assert %{
             "abroad_members" => abroad_members,
             "faction_name" => "Test",
             "flying_members" => flying_members,
             "hospital_members" => hospital_members,
             "travel_method" => "Airstrip"
           } = Tornium.Utils.tuples_to_map(render_state)

    assert %{"Hawaii" => %{"1" => %{"tid" => "1"}}} = abroad_members
    assert %{} = hospital_members
    assert %{} = flying_members

    generate_message(render_state)
  end

  test "member traveling in hospital abroad", %{vm: base_vm, notification: notification} do
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
              "description" => "In an Argentinian hospital for 9 mins",
              "details" => "Mugged by bogie",
              "state" => "Hospital",
              "color" => "red",
              "until" => 1784824771
            }
          }
        }
      })
      # Parameters
      |> Lua.set!(["TRAVEL_METHOD"], 2)
      # Internal notification data
      |> Lua.set!(["state"], %{initialized: true})

    assert {[true, render_state, passthrough_state], _vm} = Lua.eval!(vm, notification.code)

    assert %{
             "initialized" => initialized,
             "members" => members
           } =
             Tornium.Utils.tuples_to_map(passthrough_state)

    assert true = initialized

    assert %{
             "Argentinian hospital" => %{
               "1" => %{"landed" => true, "name" => "Chedburn", "tid" => "1"}
             }
           } = members

    assert %{
             "abroad_members" => abroad_members,
             "faction_name" => "Test",
             "flying_members" => flying_members,
             "hospital_members" => hospital_members,
             "travel_method" => "Airstrip"
           } = Tornium.Utils.tuples_to_map(render_state)

    assert %{} = abroad_members
    assert %{"Argentinian hospital" => %{"1" => %{"tid" => "1"}}} = hospital_members
    assert %{} = flying_members

    generate_message(render_state)
  end

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
              "details" => "",
              "state" => "Traveling",
              "color" => "blue",
              "until" => 0
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
