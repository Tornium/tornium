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

import Config

config :tornium,
  ecto_repos: [Tornium.Repo],
  generators: [timestamp_type: :utc_datetime, binary_id: true],
  env: config_env()

config :tornium, :logger, [
  {
    :handler,
    :loki_telemetry,
    :logger_std_h,
    %{
      config: %{
        file: ~c".telemetry.log",
        filesync_repeat_interval: 5000,
        file_check: 5000,
        max_no_bytes: 10_000_000,
        max_no_files: 5,
        compress_on_rotate: true
      },
      formatter: {LoggerJSON.Formatters.Basic, metadata: :all},
      metadata: :all,
      level: :debug,
      filters: [
        telemetry_only: {&Tornium.Telemetry.Loki.filter/2, []}
      ],
      filter_default: :stop
    }
  }
]

config :logger, :console,
  format: "$time $metadata[$level] $message\n",
  metadata: [:application],
  filters: [
    ignore_telemetry: {&Tornium.Telemetry.Loki.ignore_filter/2, []}
  ],
  filter_default: :log

config :tesla,
  adapter: {Tesla.Adapter.Hackney, [recv_timeout: 30_000]}

config :tornium, Tornium.PromEx,
  # See https://hexdocs.pm/prom_ex/PromEx.Config.html for configuration details
  disabled: false,
  manual_metrics_start_delay: :no_delay,
  drop_metrics_groups: [],
  grafana: :disabled,
  metrics_server: [
    port: 4021,
    path: "/metrics",
    protocol: :http,
    auth_strategy: :none
  ]

config :tornium, Oban,
  engine: Oban.Engines.Basic,
  queues: [faction_processing: 20, user_processing: 20, notifications: 20, scheduler: 5],
  repo: Tornium.Repo,
  shutdown_grace_period: :timer.seconds(30),
  plugins: [
    {Oban.Plugins.Cron,
     crontab: [
       {"* * * * *", Tornium.Workers.NotificationScheduler},
       {"0 * * * *", Tornium.Workers.OCMigrationCheck},
       {"* * * * *", Tornium.Workers.OCUpdateScheduler},
       {"*/5 * * * *", Tornium.Workers.OCUpdateScheduler},
       {"0 12 * * *", Tornium.Workers.OCCPRUpdateScheduler}
     ]},
    {Oban.Plugins.Pruner, max_age: 60 * 60 * 24},
    {Oban.Plugins.Lifeline, rescue_after: :timer.minutes(1), interval: 30_000}
  ]

config :tornium, Tornium.Web.Endpoint,
  url: [ip: {127, 0, 0, 1}, port: 4000],
  adapter: Bandit.PhoenixAdapter,
  pubsub_server: Tornium.Web.PubSub,
  live_view: [signing_salt: "z8I4+/aT"]

# Use Jason for JSON parsing in Phoenix
config :phoenix, :json_library, Jason

# Import environment specific config. This must remain at the bottom
# of this file so it overrides the configuration defined above.
import_config "#{config_env()}.exs"
