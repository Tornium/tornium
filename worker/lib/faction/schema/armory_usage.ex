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

defmodule Tornium.Schema.ArmoryUsage do
  @moduledoc """
  Logs of usage of items and points from the faction armory.
  """

  use Ecto.Schema
  alias Tornium.Repo

  @typedoc """
  Possible actions in the faction news with the following mapping:

  "used" => `:use`
  "loaned" => `:loan`
  "returned" => `:return`
  "filled" => `:fill`
  "give" => `:give`
  "retrieved" => `:retrieve`
  """
  @type actions :: :use | :loan | :return | :fill | :give | :retrieve

  @type t :: %__MODULE__{
          timestamp: DateTime.t(),
          id: String.t(),
          action: actions(),
          user_id: non_neg_integer(),
          user: Tornium.Schema.User.t(),
          recipient_id: non_neg_integer(),
          recipient: Tornium.Schema.User.t(),
          faction_id: non_neg_integer(),
          faction: Tornium.Schema.Faction.t(),
          item_id: non_neg_integer() | nil,
          item: Tornium.Schema.Item.t() | nil,
          is_energy_refill: boolean(),
          is_nerve_refill: boolean(),
          quantity: non_neg_integer()
        }

  @primary_key {:id, :string, autogenerate: false}
  schema "armory_usage" do
    field(:timestamp, :utc_datetime)
    field(:action, Ecto.Enum, values: [:use, :loan, :return, :fill, :give, :retrieve])

    belongs_to(:user, Tornium.Schema.User, references: :tid)
    belongs_to(:recipient, Tornium.Schema.User, references: :tid)
    belongs_to(:faction, Tornium.Schema.Faction, references: :tid)

    belongs_to(:item, Tornium.Schema.Item, references: :tid)
    field(:is_energy_refill, :boolean)
    field(:is_nerve_refill, :boolean)

    field(:quantity, :integer)
  end

  @doc """
  Insert multiple `Tornium.Faction.News.ArmoryAction` news logs for a specific fction.
  """
  @spec insert_all(news :: [Tornium.Faction.News.ArmoryAction.t()], faction_id :: non_neg_integer()) ::
          {non_neg_integer(), nil | [term()]}
  def insert_all([%Tornium.Faction.News.ArmoryAction{} | _] = news, faction_id) when is_integer(faction_id) do
    # We want to ensure that the users and recipients of the armory news are already in the database before
    # inserting the news to prevent foreign key violations.
    news
    |> Enum.flat_map(fn %Tornium.Faction.News.ArmoryAction{user_id: user_id, recipient_id: recipient_id} ->
      [user_id, recipient_id]
    end)
    |> Enum.reject(&is_nil/1)
    |> Enum.map(&{&1, nil})
    |> Tornium.Schema.User.ensure_exists()

    mapped_news =
      Enum.map(news, fn %Tornium.Faction.News.ArmoryAction{} = armory_news -> map(armory_news, faction_id) end)

    Repo.insert_all(__MODULE__, mapped_news, on_conflict: :nothing, conflict_target: [:id])
  end

  def insert_all([] = _news, faction_id) when is_integer(faction_id) do
    {0, []}
  end

  @doc """
  Map an `ArmoryAction` struct to a `ArmoryUsage` Ecto struct.
  """
  @spec map(news :: Tornium.Faction.News.ArmoryAction.t(), faction_id :: non_neg_integer()) :: map()
  def map(%Tornium.Faction.News.ArmoryAction{} = news, faction_id) when is_integer(faction_id) do
    news
    |> Map.put(:faction_id, faction_id)
    |> Map.delete(:__struct__)
    |> remap_armory_item()
  end

  @spec remap_armory_item(news :: map()) :: map()
  defp remap_armory_item(%{item_id: :energy_refill} = news) do
    news
    |> Map.put(:item_id, nil)
    |> Map.put(:is_energy_refill, true)
  end

  defp remap_armory_item(%{item_id: :nerve_refill} = news) do
    news
    |> Map.put(:item_id, nil)
    |> Map.put(:is_nerve_refill, true)
  end

  defp remap_armory_item(%{item_id: item_id} = news) when is_integer(item_id) do
    news
  end
end
