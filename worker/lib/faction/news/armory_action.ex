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

defmodule Tornium.Faction.News.ArmoryAction do
  @moduledoc """
  Struct containing parsed `armoryAction` news.
  """

  @behaviour Tornium.Faction.News

  defstruct [:timestamp, :id, :action, :user_id, :item_id, :quantity]

  @typedoc """
  The item ID of the item used from the armory or the type of refill used.
  """
  @type armory_item :: non_neg_integer() | :energy_refill | :nerve_refill

  @type t :: %__MODULE__{
          timestamp: DateTime.t(),
          id: String.t(),
          action: Tornium.Schema.ArmoryUsage.actions(),
          user_id: non_neg_integer(),
          item_id: armory_item(),
          quantity: non_neg_integer()
        }

  @impl Tornium.Faction.News
  def parse(%Torngen.Client.Schema.FactionNews{timestamp: timestamp, text: text, id: id} = _news) do
    %{
      user_id: user_id,
      action: action,
      item_id: item_id,
      quantity: quantity
    } =
      text
      |> Floki.parse_fragment!()
      |> do_parse_text()

    %__MODULE__{
      timestamp: DateTime.from_unix!(timestamp),
      id: id,
      action: action,
      user_id: user_id,
      item_id: item_id,
      quantity: quantity
    }
  end

  @spec do_parse_text(tree :: Floki.html_tree()) :: %{
          user_id: non_neg_integer(),
          action: Tornium.Schema.ArmoryUsage.actions(),
          item_id: armory_item(),
          quantity: non_neg_integer()
        }
  defp do_parse_text([{"a", [{"href", faction_member_link}], [_faction_member_name]}, text_remainder] = _tree) do
    # e.g. for "<a href = \"http://www.torn.com/profiles.php?XID=3870167\">Kagat</a> used one of the faction's Blood Bag : O+ items"
    # faction_member_link = http://www.torn.com/profiles.php?XID=3870167
    # faction_member_name = Kagat
    # text_remainder = " used one of the faction's Blood Bag : O+ items"

    user_id =
      faction_member_link
      |> URI.parse()
      |> Map.get(:query)
      |> URI.decode_query()
      |> Map.get("XID")
      |> String.to_integer()

    %{
      action: action,
      quantity: quantity,
      item_name: item_name
    } =
      text_remainder
      |> String.trim()
      |> text_action_item()

    item_id =
      case item_name do
        :energy_refill ->
          :energy_refill

        :nerve_refill ->
          :nerve_refill

        _ when is_binary(item_name) ->
          Tornium.Item.NameCache.get_by_name(item_name)
      end

    %{user_id: user_id, action: action, item_id: item_id, quantity: quantity}
  end

  @spec text_action_item(text :: String.t()) ::
          %{
            action: Tornium.Schema.ArmoryUsage.actions(),
            quantity: non_neg_integer(),
            item_name: armory_item() | String.t()
          }
          | nil
  defp text_action_item("used " <> suffixed_item_string = text) when is_binary(text) do
    split_item_string =
      String.split(suffixed_item_string, [" of the faction's ", " items", " to refill their "], trim: true)

    case split_item_string do
      ["one", item_name] ->
        %{
          action: :use,
          quantity: 1,
          item_name: item_name
        }

      [count, "points", "energy"] ->
        %{
          action: :use,
          quantity: String.to_integer(count),
          item_name: :energy_refill
        }

      [count, "points", "nerve"] ->
        # eg: "<a href = \"http://www.torn.com/profiles.php?XID=2383326\">tiksan</a> used 30 of the faction's points to refill their nerve"
        %{
          action: :use,
          quantity: String.to_integer(count),
          item_name: :nerve_refill
        }
    end
  end

  defp text_action_item("filled one of the faction's " <> suffixed_item_string = text) when is_binary(text) do
    [item_name] = String.split(suffixed_item_string, " items", trim: true)

    %{
      action: :fill,
      quantity: 1,
      item_name: item_name
    }
  end

  defp text_action_item("loaned " <> suffixed_item_string = text) when is_binary(text) do
    [item_name_quantity, _recipient] =
      String.split(suffixed_item_string, [" to ", " from the faction armory"], trim: true)

    # loaned 1x Thompson to themselves from the faction armory
    [item_quantity, item_name] = String.split(item_name_quantity, "x ", trim: true)

    %{
      action: :loan,
      quantity: String.to_integer(item_quantity),
      item_name: item_name
    }
  end

  defp text_action_item("returned " <> item_name_quantity = text) when is_binary(text) do
    [item_quantity, item_name] = String.split(item_name_quantity, "x ", trim: true)

    %{
      action: :return,
      quantity: String.to_integer(item_quantity),
      item_name: item_name
    }
  end
end
