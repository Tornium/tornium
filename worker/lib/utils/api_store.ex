defmodule Tornium.API.Store do
  @moduledoc """
  GenServer to retain API call responses.

  `Tornium.API.Store` will store Torn API call responses until an Oban Job retrieves the response by API call ID or until the response expires.
  """

  # TODO: Document this genserver
  # TODO: Write tests for this genserver

  @default_ttl 60

  use GenServer

  defmodule StoredResponse do
    @moduledoc false

    defstruct [:response, :expires_at]

    @type t :: %__MODULE__{
            response: map() | :expired | :not_ready,
            expires_at: DateTime.t()
          }
  end

  @spec start_link(opts :: term()) :: GenServer.on_start()
  def start_link(_opts) do
    GenServer.start_link(__MODULE__, :ok, name: __MODULE__)
  end

  # TODO: Document and type `create()`
  def create(api_call_id) do
    create(api_call_id, @default_ttl)
  end

  def create(api_call_id, ttl) when is_integer(ttl) do
    expires_at = DateTime.utc_now() |> DateTime.add(ttl, :second)
    create(api_call_id, expires_at)
  end

  def create(api_call_id, %DateTime{} = expires_at) do
    GenServer.cast(__MODULE__, {:create, api_call_id, expires_at})
  end

  @doc """
  Insert an API response into the GenServer.
  """
  @spec insert(result :: map(), api_call_id :: String.t()) :: term()
  def insert(result, api_call_id) do
    GenServer.cast(__MODULE__, {:insert, result, api_call_id})
  end

  # TODO: Document and type `pop()`
  def pop(api_call_id) do
    GenServer.call(__MODULE__, {:pop, api_call_id})
  end

  @impl true
  def init(_opts) do
    {:ok, %{}}
  end

  @impl true
  def handle_cast({:create, api_call_id, %DateTime{} = expires_at}, %{} = state) do
    {:noreply, Map.put_new(state, api_call_id, %StoredResponse{response: :not_ready, expires_at: expires_at})}
  end

  @impl true
  def handle_cast({:insert, result, api_call_id}, %{} = state) do
    stored_response = Map.get(state, api_call_id)
    {:noreply, Map.put(state, api_call_id, %StoredResponse{stored_response | response: result})}
  end

  @impl true
  def handle_call({:pop, api_call_id}, _from, %{} = state) do
    {value, updated_state} =
      case Map.get(state, api_call_id) do
        %StoredResponse{response: value} when is_map(value) ->
          {_, updated_state} = Map.pop(state, api_call_id)
          {value, updated_state}

        %StoredResponse{response: value} ->
          {value, state}

        _ ->
          {nil, state}
      end

    {:reply, value, updated_state}
  end

  # TODO: Add timer to automatically remove expired responses
end
