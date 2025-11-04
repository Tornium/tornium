defmodule Tornium.Item.NameCache do
  @moduledoc """
  A bidirection item name cache for 

  ```
  Item ID <=> Item Name
  ```
  """

  use Agent

  @type state :: %{
          forward: %{non_neg_integer() => String.t()},
          backward: %{String.t() => non_neg_integer()},
          ttl: non_neg_integer(),
          ttl_unit: :day | :hour | :minute | System.time_unit(),
          expiration: DateTime.t()
        }

  @spec start_link(opts :: keyword()) :: Agent.on_start()
  def start_link(opts \\ []) do
    ttl = Keyword.get(opts, :ttl, 3600)
    ttl_unit = Keyword.get(opts, :ttl_unit, :second)

    Agent.start(
      fn ->
        %{
          forward: %{},
          backward: %{},
          ttl: ttl,
          ttl_unit: ttl_unit,
          expiration: nil
        }
      end,
      name: __MODULE__
    )
  end

  @doc """
  Get the item name by its ID.
  """
  @spec get_by_id(item_id :: non_neg_integer()) :: String.t()
  def get_by_id(item_id) when is_integer(item_id) do
    ensure_fresh()
    Agent.get(__MODULE__, &Map.get(&1.forward, item_id))
  end

  @doc """
  Get the item ID by its name.
  """
  @spec get_by_name(item_name :: String.t()) :: non_neg_integer()
  def get_by_name(item_name) when is_binary(item_name) do
    ensure_fresh()
    Agent.get(__MODULE__, &Map.get(&1.backward, item_name))
  end

  @doc """
  Get all items in the map.
  """
  @spec all() :: %{non_neg_integer() => String.t()}
  def all() do
    Agent.get(__MODULE__, & &1.forward)
  end

  @doc """
  Update the items in the bimap if the data is expired.

  This is a non-blocking operation.
  """
  @spec ensure_fresh() :: term()
  def ensure_fresh() do
    if expired?(), do: rebuild()
  end

  def rebuild() do
    # TODO: Revert to defp and Agent.cast
    Agent.update(__MODULE__, fn %{ttl: ttl, ttl_unit: ttl_unit} = state ->
      items_forward =
        Tornium.Schema.Item.all()
        |> Enum.map(fn %Tornium.Schema.Item{tid: item_id, name: item_name} -> {item_id, item_name} end)
        |> Map.new()

      items_backward = Map.new(items_forward, fn {item_id, item_name} -> {item_name, item_id} end)

      state
      |> Map.replace!(:expiration, expiration(ttl, ttl_unit))
      |> Map.replace!(:forward, items_forward)
      |> Map.replace!(:backward, items_backward)
    end)
  end

  @spec expired?() :: boolean()
  defp expired?() do
    expiration = Agent.get(__MODULE__, & &1.expiration)

    case expiration do
      nil ->
        true

      %DateTime{} ->
        DateTime.after?(DateTime.utc_now(), expiration)
    end
  end

  @spec expiration(
          ttl :: non_neg_integer(),
          ttl_unit :: :day | :hour | :minute | System.time_unit()
        ) :: DateTime.t()
  defp expiration(ttl, ttl_unit) when is_integer(ttl) do
    DateTime.utc_now() |> DateTime.add(ttl, ttl_unit)
  end
end
