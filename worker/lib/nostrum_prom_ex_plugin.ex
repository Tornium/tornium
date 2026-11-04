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

defmodule Tornium.Nostrum.PromEx do
  @moduledoc """
  A PromEx plugin for the Nostrum Discord library.
  """

  use PromEx.Plugin

  # Nostrum events
  @api_request_start [:nostrum, :api, :request, :start]
  @api_request_stop [:nostrum, :api, :request, :stop]
  @api_request_exception [:nostrum, :api, :request, :exception]

  @ratelimiter_connected [:nostrum, :ratelimiter, :connected]
  @ratelimiter_connect_timeout [:nostrum, :ratelimiter, :connect_timeout]
  @ratelimiter_disconnected [:nostrum, :ratelimiter, :disconnected]
  @ratelimiter_postponed [:nostrum, :ratelimiter, :postponed]

  @shard_connected [:nostrum, :gateway, :shard, :connected]
  @shard_disconnected [:nostrum, :gateway, :shard, :disconnected]
  @shard_heartbeat [:nostrum, :gateway, :shard, :heartbeat]

  # Events emitted by this plugin
  @proxy_api_request_stop [:prom_ex, :plugin, :nostrum, :api, :request, :stop]
  @proxy_ratelimiter_status [:prom_ex, :plugin, :nostrum, :ratelimiter, :status]
  @proxy_shard_status [:prom_ex, :plugin, :nostrum, :gateway, :shard, :status]
  @poll_shard_latency [:prom_ex, :plugin, :nostrum, :gateway, :shard, :latency]

  @proxied_events [
    @api_request_start,
    @api_request_stop,
    @api_request_exception,
    @ratelimiter_connected,
    @ratelimiter_connect_timeout,
    @ratelimiter_disconnected,
    @shard_connected,
    @shard_disconnected
  ]

  @proxy_handler_id {__MODULE__, :proxy}

  @default_duration_buckets_ms [50, 100, 250, 500, 1_000, 2_500, 5_000, 10_000, 30_000]

  @impl true
  def event_metrics(opts) do
    otp_app = Keyword.fetch!(opts, :otp_app)
    metric_prefix = Keyword.get(opts, :metric_prefix, PromEx.metric_prefix(otp_app, :nostrum))
    duration_unit = Keyword.get(opts, :duration_unit, :millisecond)

    duration_buckets = Keyword.get_lazy(opts, :duration_buckets, fn -> default_duration_buckets(duration_unit) end)

    [
      api_event_metrics(metric_prefix, duration_unit, duration_buckets),
      ratelimiter_event_metrics(metric_prefix),
      gateway_event_metrics(metric_prefix)
    ]
  end

  @impl true
  def polling_metrics(opts) do
    poll_rate = Keyword.get(opts, :poll_rate, 5_000)
    bots = Keyword.get(opts, :bots, [])

    case bots do
      [] ->
        []

      bots ->
        Polling.build(
          :nostrum_shard_latency_poll_metrics,
          poll_rate,
          {__MODULE__, :execute_shard_latency_metrics, [bots]},
          [
            last_value(
              [:nostrum, :gateway, :shard, :latency, :milliseconds],
              event_name: @poll_shard_latency,
              measurement: :latency,
              description: "The most recent gateway heartbeat round-trip time of the shard.",
              tag_values: &shard_tag_values/1,
              tags: [:bot, :shard]
            )
          ]
        )
    end
  end

  defp api_event_metrics(metric_prefix, duration_unit, duration_buckets) do
    duration_unit_plural = PromEx.Utils.make_plural_atom(duration_unit)

    Event.build(
      :nostrum_api_event_metrics,
      [
        distribution(
          metric_prefix ++ [:api, :request, :duration, duration_unit_plural],
          event_name: @proxy_api_request_stop,
          measurement: :duration,
          description:
            "The time taken by Discord API requests made through Nostrum, including time queued in the ratelimiter.",
          reporter_options: [buckets: duration_buckets],
          tag_values: &api_tag_values(&1),
          tags: [:bot, :method, :route, :status],
          unit: {:native, duration_unit}
        ),
        counter(
          metric_prefix ++ [:api, :request, :exception, :total],
          event_name: @api_request_exception,
          description: "The number of Discord API requests that raised, threw or exited.",
          tag_values: &api_exception_tag_values(&1),
          tags: [:bot, :method, :route, :kind, :reason]
        )
      ]
    )
  end

  defp ratelimiter_event_metrics(metric_prefix) do
    Event.build(
      :nostrum_ratelimiter_event_metrics,
      [
        counter(
          metric_prefix ++ [:ratelimiter, :connected, :total],
          event_name: @ratelimiter_connected,
          description: "The number of times the ratelimiter connected to the Discord API.",
          tag_values: &bot_tag_values/1,
          tags: [:bot]
        ),
        counter(
          metric_prefix ++ [:ratelimiter, :connect_timeout, :total],
          event_name: @ratelimiter_connect_timeout,
          description: "The number of times the ratelimiter timed out connecting to the Discord API.",
          tag_values: &bot_tag_values/1,
          tags: [:bot]
        ),
        counter(
          metric_prefix ++ [:ratelimiter, :disconnected, :total],
          event_name: @ratelimiter_disconnected,
          description: "The number of times the ratelimiter lost its connection to the Discord API.",
          tag_values: &bot_tag_values/1,
          tags: [:bot]
        ),
        counter(
          metric_prefix ++ [:ratelimiter, :postponed, :total],
          event_name: @ratelimiter_postponed,
          description: "The number of requests the ratelimiter delayed because a ratelimit was exhausted.",
          tag_values: &postponed_tag_values(&1),
          tags: [:bot, :route, :global]
        ),
        last_value(
          metric_prefix ++ [:ratelimiter, :connection, :status],
          event_name: @proxy_ratelimiter_status,
          measurement: :up,
          description: "Whether the ratelimiter's HTTP connection is up (1) or down (0).",
          tag_values: &bot_tag_values/1,
          tags: [:bot]
        )
      ]
    )
  end

  defp gateway_event_metrics(metric_prefix) do
    Event.build(
      :nostrum_gateway_event_metrics,
      [
        counter(
          metric_prefix ++ [:gateway, :shard, :connected, :total],
          event_name: @shard_connected,
          description: "The number of times a shard (re)connected to the gateway.",
          tag_values: &shard_tag_values/1,
          tags: [:bot, :shard]
        ),
        counter(
          metric_prefix ++ [:gateway, :shard, :disconnected, :total],
          event_name: @shard_disconnected,
          description: "The number of times a shard disconnected from the gateway.",
          tag_values: &shard_disconnect_tag_values/1,
          tags: [:bot, :shard, :reason]
        ),
        counter(
          metric_prefix ++ [:gateway, :shard, :heartbeat, :total],
          event_name: @shard_heartbeat,
          description: "The number of heartbeats a shard has sent to the gateway.",
          tag_values: &shard_tag_values/1,
          tags: [:bot, :shard]
        ),
        last_value(
          metric_prefix ++ [:gateway, :shard, :sequence],
          event_name: @shard_heartbeat,
          measurement: :seq,
          description: "The gateway sequence number the shard last sent in a heartbeat.",
          tag_values: &shard_tag_values/1,
          tags: [:bot, :shard]
        ),
        last_value(
          metric_prefix ++ [:gateway, :shard, :connection, :status],
          event_name: @proxy_shard_status,
          measurement: :up,
          description: "Whether the shard's gateway connection is up (1) or down (0).",
          tag_values: &shard_tag_values/1,
          tags: [:bot, :shard]
        )
      ]
    )
  end

  def handle_proxy_event(@ratelimiter_connected, _measurements, metadata, _config) do
    :telemetry.execute(@proxy_ratelimiter_status, %{up: 1}, metadata)
  end

  def handle_proxy_event(event, _measurements, metadata, _config)
      when event in [@ratelimiter_disconnected, @ratelimiter_connect_timeout] do
    :telemetry.execute(@proxy_ratelimiter_status, %{up: 0}, metadata)
  end

  def handle_proxy_event(@shard_connected, _measurements, metadata, _config) do
    :telemetry.execute(@proxy_shard_status, %{up: 1}, metadata)
  end

  def handle_proxy_event(@shard_disconnected, _measurements, metadata, _config) do
    :telemetry.execute(@proxy_shard_status, %{up: 0}, metadata)
  end

  def handle_proxy_event(_event, _measurements, _metadata, _config), do: :ok

  @doc false
  def execute_shard_latency_metrics(:auto) do
    safely(fn ->
      Enum.each(Nostrum.Bot.fetch_all_bots(), &poll_bot_shard_latencies(&1.name))
    end)
  end

  def execute_shard_latency_metrics(bots) when is_list(bots) do
    Enum.each(bots, &poll_bot_shard_latencies/1)
  end

  defp poll_bot_shard_latencies(bot) do
    safely(fn ->
      # Without this check `with_bot/2` would fall back to "the only running
      # bot" and report its latencies under the wrong name.
      if is_pid(Nostrum.Bot.fetch_bot_pid(bot)) do
        latencies = Nostrum.Bot.with_bot(bot, &Nostrum.Util.get_all_shard_latencies/0)
        emit_shard_latencies(bot, latencies)
      end
    end)
  end

  defp emit_shard_latencies(bot, latencies) do
    Enum.each(latencies, fn
      {_shard, nil} ->
        :ok

      {shard, latency} ->
        :telemetry.execute(@poll_shard_latency, %{latency: latency}, %{bot: bot, shard_number: shard})
    end)
  end

  # The bot or its shards may be (re)starting; that's not worth a log line
  # every poll, and an exit must not take down the poller.
  defp safely(fun) do
    fun.()
    :ok
  rescue
    _ -> :ok
  catch
    :exit, _ -> :ok
  end

  # ---------------------------------------------------------------------------
  # Tag values
  # ---------------------------------------------------------------------------

  defp api_tag_values(metadata) do
    %{
      bot: label(Map.get(metadata, :bot)),
      method: method_label(Map.get(metadata, :method)),
      route: route_label(Map.get(metadata, :route)),
      status: label(Map.get(metadata, :status))
    }
  end

  defp api_exception_tag_values(metadata) do
    kind = Map.get(metadata, :kind)

    metadata
    |> api_tag_values()
    |> Map.delete(:status)
    |> Map.merge(%{
      kind: label(kind),
      reason: exception_reason(kind, Map.get(metadata, :reason), Map.get(metadata, :stacktrace, []))
    })
  end

  defp postponed_tag_values(metadata) do
    %{
      bot: label(Map.get(metadata, :bot)),
      route: route_label(Map.get(metadata, :major_route)),
      global: to_string(Map.get(metadata, :global) == true)
    }
  end

  defp bot_tag_values(metadata) do
    %{bot: label(Map.get(metadata, :bot))}
  end

  defp shard_tag_values(metadata) do
    %{
      bot: label(Map.get(metadata, :bot)),
      shard: label(Map.get(metadata, :shard_number))
    }
  end

  defp shard_disconnect_tag_values(metadata) do
    metadata
    |> shard_tag_values()
    |> Map.put(:reason, reason_label(Map.get(metadata, :reason)))
  end

  defp label(nil), do: "unknown"
  defp label(value) when is_atom(value), do: PromEx.Utils.normalize_module_name(value)
  defp label(value) when is_binary(value), do: value
  defp label(value) when is_number(value), do: to_string(value)
  defp label(value), do: inspect(value)

  defp method_label(method) when is_atom(method) do
    method
    |> Atom.to_string()
    |> String.upcase()
  end

  defp method_label(method) when is_binary(method), do: String.upcase(method)
  defp method_label(_), do: "unknown"

  # Disconnect reasons are documented as atoms; anything else is lumped together
  # rather than risking an unbounded label.
  defp reason_label(reason) when is_atom(reason), do: label(reason)
  defp reason_label(_), do: "other"

  defp route_label(route) when is_binary(route), do: normalize_route(route)
  defp route_label(_route), do: "unknown"

  defp exception_reason(:error, reason, stacktrace) do
    %module{} = Exception.normalize(:error, reason, stacktrace)
    PromEx.Utils.normalize_module_name(module)
  end

  defp exception_reason(:exit, reason, _stacktrace) when is_atom(reason), do: Macro.camelize(Atom.to_string(reason))

  defp exception_reason(:exit, {reason, _}, _stacktrace) when is_atom(reason),
    do: Macro.camelize(Atom.to_string(reason))

  defp exception_reason(:exit, _reason, _stacktrace), do: "UnknownExit"
  defp exception_reason(:throw, _reason, _stacktrace), do: "UnknownThrow"
  defp exception_reason(_kind, _reason, _stacktrace), do: "UnknownException"

  # ---------------------------------------------------------------------------
  # Route normalization
  # ---------------------------------------------------------------------------

  @doc """
  Normalizes a Discord API route into a low-cardinality label value.

  Handles both raw routes (`Nostrum.Api` metadata) and Nostrum's ratelimit
  bucket keys (`:major_route` metadata, e.g. `"delete:/channels/123/messages/_id"`).

      iex> PromEx.Plugins.Nostrum.normalize_route("/channels/81384788765712384/messages/1234567890123456789")
      "/channels/:id/messages/:id"

      iex> PromEx.Plugins.Nostrum.normalize_route("/channels/81384788765712384/messages/1/reactions/%F0%9F%91%8D/@me")
      "/channels/:id/messages/:id/reactions/:emoji/@me"

      iex> PromEx.Plugins.Nostrum.normalize_route("/interactions/1234567890123456789/aW50ZXJhY3Rpb24/callback")
      "/interactions/:id/:token/callback"
  """
  @spec normalize_route(String.t()) :: String.t()
  def normalize_route(route) when is_binary(route) do
    [path | _query] = String.split(route, "?", parts: 2)

    normalized =
      path
      |> replace(~r{/webhooks/([^/]+)/[^/]+}, "/webhooks/\\1/:token")
      |> replace(~r{/interactions/([^/]+)/[^/]+/callback}, "/interactions/\\1/:token/callback")
      |> replace(~r{/reactions/[^/]+}, "/reactions/:emoji")
      |> replace(~r{/invites/[^/]+}, "/invites/:code")
      |> replace(~r{/(?:\d+|_id)(?=/|$)}, "/:id")
      |> replace(~r"/{2,}", "/")

    case normalized do
      "/" -> "/"
      other -> String.trim_trailing(other, "/")
    end
  end

  defp replace(string, regex, replacement), do: Regex.replace(regex, string, replacement)

  defp default_duration_buckets(:millisecond), do: @default_duration_buckets_ms
  defp default_duration_buckets(:second), do: Enum.map(@default_duration_buckets_ms, &(&1 / 1_000))
  defp default_duration_buckets(:microsecond), do: Enum.map(@default_duration_buckets_ms, &(&1 * 1_000))
  defp default_duration_buckets(:nanosecond), do: Enum.map(@default_duration_buckets_ms, &(&1 * 1_000_000))
end
