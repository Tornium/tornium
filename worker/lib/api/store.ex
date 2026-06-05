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

defmodule Tornium.API.Store do
  @moduledoc """
  Sharded GenServer to retain API call responses.

  `Tornium.API.Store` will store Torn API call responses until an Oban Job retrieves the
  response by API call ID or until the response expires.
  """

  # TODO: Document this genserver
  # TODO: Write tests for this genserver

  @default_ttl 300
  @shards Application.compile_env(:tornium, :api_shards, 2)

  use GenServer
  require Logger

  defmodule StoredResponse do
    @moduledoc false

    defstruct [:response, :expires_at]

    @type t :: %__MODULE__{
            response: map() | :expired | :not_ready,
            expires_at: DateTime.t()
          }
  end

  @spec via(shard :: non_neg_integer()) :: tuple()
  defp via(shard) when is_integer(shard) do
    {:via, Horde.Registry, {Tornium.API.Registry, {__MODULE__, shard}}}
  end

  @spec via(api_call_id :: String.t()) :: tuple()
  defp via(api_call_id) when is_binary(api_call_id) do
    api_call_id
    |> :erlang.phash2(@shards)
    |> via()
  end

  @doc """
  ## Options
    * `:shard` - Index of the shard of the `Tornium.API.Store`.
  """
  @spec start_link(shard :: non_neg_integer()) :: GenServer.on_start()
  def start_link(shard) when is_integer(shard) do
    GenServer.start_link(__MODULE__, shard, name: via(shard))
  end

  @doc """
  Create a `StoredResponse` for the API call ID.

  The created `StoredResponse` for the provided API call ID that will be marked as `:not_ready`
  until updated after receiving a response from the API. This `StoredResponse` will have the default
  TTL.
  """
  @spec create(api_call_id :: String.t()) :: :ok
  def create(api_call_id) do
    create(api_call_id, @default_ttl)
  end

  @doc """
  Create a `StoredResponse` for the API call ID with a custom TTL.

  The created `StoredResponse` for the provided API call ID that will be marked as `:not_ready`
  until updated after receiving a response from the API through `insert/2`. This `StoredResponse`
  will expire at the provided `Datetime` or after TTL seconds from when invoked.
  """
  @spec create(api_call_id :: String.t(), ttl :: integer() | DateTime.t()) :: :ok
  def create(api_call_id, ttl) when is_integer(ttl) do
    expires_at = DateTime.utc_now() |> DateTime.add(ttl, :second)
    create(api_call_id, expires_at)
  end

  def create(api_call_id, %DateTime{} = expires_at) do
    GenServer.cast(via(api_call_id), {:create, api_call_id, expires_at})
  end

  @doc """
  Insert an API response into the GenServer.

  Insert an API response into the `StoredResponse` for the provided API call ID. Once the API response is 
  inserted, the response can be retrieved with `pop/1`.
  """
  @spec insert(result :: map(), api_call_id :: String.t()) :: term()
  def insert(result, api_call_id) do
    GenServer.cast(via(api_call_id), {:insert, result, api_call_id})
  end

  @doc """
  Pop an API response from the GenServer.

  Remove and return the API response corresponding to the provided API call ID if it exists and 
  is ready. If the response is not ready, `nil` will be returned instead.
  """
  @spec pop(api_call_id :: String.t()) :: map() | :not_ready | :expired | nil
  def pop(api_call_id) do
    GenServer.call(via(api_call_id), {:pop, api_call_id})
  end

  @impl true
  def init(shard) when is_integer(shard) do
    Logger.info("Starting Tornium.API.Store shard ##{shard}")

    table_name = :"#{__MODULE__}_#{shard}"
    table = :ets.new(table_name, [:set, :private, read_concurrency: true, write_concurrency: true])

    :timer.send_interval(15_000, :expire)

    {:ok, %{shard: shard, table: table}}
  end

  @impl true
  def handle_cast({:create, api_call_id, %DateTime{} = expires_at}, %{table: table} = state) do
    stored_response = %StoredResponse{response: :not_ready, expires_at: expires_at}

    :ets.insert_new(table, {api_call_id, stored_response})

    {:noreply, state}
  end

  @impl true
  def handle_cast({:insert, result, api_call_id}, %{table: table} = state) do
    case :ets.lookup(table, api_call_id) do
      [{^api_call_id, %StoredResponse{} = stored_response}] ->
        :ets.insert(table, {api_call_id, %{stored_response | response: result}})

      [] ->
        # TODO: Add more details to the log
        Logger.debug("Unable to insert response for #{api_call_id} into the API store")
    end

    {:noreply, state}
  end

  @impl true
  def handle_call({:pop, api_call_id}, _from, %{table: table} = state) do
    response =
      case :ets.take(table, api_call_id) do
        [] ->
          nil

        [{^api_call_id, %StoredResponse{response: :not_ready} = stored_response}] ->
          :ets.insert(table, {api_call_id, stored_response})

          :not_ready

        [{^api_call_id, %StoredResponse{response: response}}] ->
          response
      end

    {:reply, response, state}
  end

  @impl true
  def handle_info(:expire, %{} = state) do
    now = DateTime.utc_now()

    :ets.foldl(
      fn {api_call_id, %StoredResponse{expires_at: expires_at}}, _acc ->
        if DateTime.after?(now, expires_at) do
          :ets.delete(state.table, api_call_id)
        end

        nil
      end,
      nil,
      state.table
    )

    {:noreply, state}
  end
end
