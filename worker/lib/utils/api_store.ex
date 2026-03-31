defmodule Tornium.API.Store do
  @moduledoc """
  GenServer to retain API call responses.

  `Tornium.API.Store` will store Torn API call responses until an `Oban.Job` retrieves the response by API call
  ID. If an `Oban.Job` or the job ID was provided when the `StoredResponse` was created, then it is assumed that
  the respective job is suspended and can be made available once a response from the API is received. If the
  response has not been retrieved, the response will expire and will be removed from the
  `Tornium.API.Store`.
  """

  # TODO: Write tests for this genserver

  @default_ttl 300

  use GenServer

  defmodule StoredResponse do
    @moduledoc false

    defstruct [:response, :expires_at, :job_id]

    @type t :: %__MODULE__{
            response: map() | :expired | :not_ready,
            expires_at: DateTime.t(),
            job_id: pos_integer() | nil
          }

    def expired?(%__MODULE__{expires_at: expires_at}) do
      DateTime.after?(DateTime.utc_now(), expires_at)
    end
  end

  @doc """
  Start the `Tornium.API.Store` GenServer.
  """
  @spec start_link(opts :: keyword()) :: GenServer.on_start()
  def start_link(opts \\ []) do
    GenServer.start_link(__MODULE__, opts, name: __MODULE__)
  end

  @doc """
  Create a `StoredResponse` for the API call ID.

  The created `StoredResponse` for the provided API call ID that will be marked as `:not_ready` until updated
  after receiving a response from the API through `insert/2`. This `StoredResponse` will expire at the provided
  `DateTime` orafter TTL seconds from when invoked if a `:ttl` is provided. Otherwise, the response will expire
  after `@default_ttl` seconds.

  ## Options
    * `:tll` - The timeout of the StoredResponse in seconds or as a `DateTime` (default: `@default_ttl`)
    * `:job_id` - The ID of the Oban job or the response of `Oban.insert` (default:  `nil`)
  """
  @spec create(api_call_id :: String.t(), opts :: keyword()) :: :ok | :error
  def create(api_call_id, opts \\ []) when is_binary(api_call_id) do
    ttl = Keyword.get(opts, :ttl, @default_ttl)
    job_id = opts |> Keyword.get(:job_id, nil) |> resolve_job_id()

    do_create(api_call_id, ttl, job_id)
  end

  defp do_create(_api_call_id, _ttl, :error) do
    :error
  end

  defp do_create(api_call_id, ttl, job_id) when is_binary(api_call_id) and is_integer(ttl) do
    expires_at = DateTime.utc_now() |> DateTime.add(ttl, :second)
    do_create(api_call_id, expires_at, job_id)
  end

  defp do_create(api_call_id, %DateTime{} = expires_at, job_id) when is_binary(api_call_id) do
    GenServer.cast(__MODULE__, {:create, api_call_id, expires_at, job_id})
  end

  defp resolve_job_id(job) do
    case job do
      nil ->
        nil

      {:ok, %Oban.Job{id: job_id}} ->
        job_id

      {:error, _} ->
        :error
    end
  end

  @doc """
  Insert an API response into the GenServer.

  Insert an API response into the `StoredResponse` for the provided API call ID. If `job_id` is provided from an
  `Oban.Job`, the relevant job will be moved to the `:available` state (from the assumed to be `:suspended`
  state). Once the API response is inserted, the response can be retrieved with `pop/1`.
  """
  @spec insert(result :: map(), api_call_id :: String.t()) :: term()
  def insert(result, api_call_id) when is_binary(api_call_id) do
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
  def handle_cast({:create, api_call_id, %DateTime{} = expires_at, job_id}, %{} = state) do
    {:noreply,
     Map.put_new(
       state,
       api_call_id,
       %StoredResponse{response: :not_ready, expires_at: expires_at, job_id: job_id}
     )}
  end

  @impl true
  def handle_cast({:insert, result, api_call_id}, %{} = state) do
    %StoredResponse{} = stored_response = Map.fetch!(state, api_call_id)

    if not is_nil(stored_response.job_id) do
      # Since the stored response's job ID is not nil, there is an Oban Job waiting on this API call. We
      # should move the respective Oban Job to the available state so that it can use this API call response.
      release_job(stored_response.job_id)
    end

    {:noreply, Map.put(state, api_call_id, %{stored_response | response: result})}
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

  @spec release_job(job_id :: pos_integer()) :: term()
  defp release_job(job_id) when is_integer(job_id) do
    # Currently, retrying the job is the only known method of releasing the Oban.Job from the suspended state
    Oban.retry_job(job_id)
  end
end
