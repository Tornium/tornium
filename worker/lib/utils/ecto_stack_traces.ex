defmodule Tornium.EctoStacktraces do
  @moduledoc """
  Source: https://elixirforum.com/t/tracking-down-slow-queries-in-ecto/58121/23?u=tiksan
  """

  def setup() do
    :ets.new(:queries_and_stacktraces, [:set, :named_table, :public])
    :telemetry.attach("ecto-stacktrace-tracking", [:tornium, :repo, :query], &handle_event/4, %{})
  end

  def filter(string) do
    {:ok, regex} =
      string
      |> Regex.escape()
      |> Regex.compile()

    find = fn {query, _stacktrace, _cast_params, _measurements} = item, acc ->
      if String.match?(query, regex) do
        [item | acc]
      else
        acc
      end
    end

    :ets.foldl(find, [], :queries_and_stacktraces)
  end

  def handle_event([:tornium, :repo, :query], measurements, metadata, _config) do
    :ets.insert(
      :queries_and_stacktraces,
      {metadata[:query], metadata[:stacktrace], metadata[:cast_params], measurements}
    )
  end
end
