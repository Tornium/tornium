defmodule Tornium.API.Store do
  @moduledoc """
  GenServer to retain API call responses.

  `Tornium.API.Store` will store Torn API call responses until an Oban Job retrieves the response by API call ID or until the response expires.
  """

  # TODO: Document this genserver
  # TODO: Write tests for this genserver

  @default_ttl 300

  use GenServer

  defmodule StoredResponse do
    @moduledoc false

    defstruct [:response, :expires_at]

    @type t :: %__MODULE__{
            response: map() | :expired | :not_ready,
            expires_at: DateTime.t()
          }

    def expired?(%__MODULE__{expires_at: expires_at}) do
      DateTime.after?(DateTime.utc_now(), expires_at)
    end
  end

  @spec start_link(opts :: keyword()) :: GenServer.on_start()
  def start_link(opts \\ []) do
    GenServer.start_link(__MODULE__, opts, name: __MODULE__)
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
  until updated after receiving a response from the API through `insert/2`. This `StoredResponse` will expire at the 
  provided `Datetime` or after TTL seconds from when invoked.
  """
  @spec create(api_call_id :: String.t(), ttl :: integer() | DateTime.t()) :: :ok
  def create(api_call_id, ttl) when is_integer(ttl) do
    expires_at = DateTime.utc_now() |> DateTime.add(ttl, :second)
    create(api_call_id, expires_at)
  end

  def create(api_call_id, %DateTime{} = expires_at) do
    GenServer.cast(__MODULE__, {:create, api_call_id, expires_at})
  end

  @doc """
  Insert an API response into the GenServer.

  Insert an API response into the `StoredResponse` for the provided API call ID. Once the API response is 
  inserted, the response can be retrieved with `pop/1`.
  """
  @spec insert(result :: map(), api_call_id :: String.t()) :: term()
  def insert(result, api_call_id) do
    GenServer.cast(__MODULE__, {:insert, result, api_call_id})
  end

  @doc """
  Pop an API response from the GenServer.

  Remove and return the API response corresponding to the provided API call ID if it exists and 
  is ready. If the response is not ready, `nil` will be returned instead.
  """
  @spec pop(api_call_id :: String.t()) :: map() | :not_ready | :expired | nil
  def pop(api_call_id) do
    GenServer.call(__MODULE__, {:pop, api_call_id})
  end

  @doc false
  @spec expire() :: term()
  def expire() do
    send(__MODULE__, :expire)
  end

  @impl true
  def init(opts \\ []) do
    if Keyword.get(opts, :expires, true) do
      :timer.send_interval(15_000, :expire)
    end

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
        %StoredResponse{response: :not_ready} ->
          {:not_ready, state}

        %StoredResponse{response: :expired} ->
          {:expired, state}

        %StoredResponse{response: value} when is_map(value) ->
          {_, updated_state} = Map.pop(state, api_call_id)
          {value, updated_state}

        response when is_nil(response) ->
          {nil, state}
      end

    {:reply, value, updated_state}
  end

  @impl true
  def handle_info(:expire, %{} = state) do
    {
      :noreply,
      state
      |> Enum.reject(fn {_api_call_id, %StoredResponse{} = stored_response} ->
        StoredResponse.expired?(stored_response)
      end)
      |> Map.new()
    }
  end
end
