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

defmodule Tornium.Application do
  @moduledoc false

  use Application

  @spec start(Application.start_type(), term()) :: {:ok, pid()} | {:ok, pid(), Application.state()} | {:error, term()}
  def start(_type, _args) do
    Logger.add_handlers(:tornium)

    # Attach the default loggers from :telemetry before the start of the children
    Tornium.Telemetry.attach_default_logger()
    Tornium.Telemetry.VerificationLogs.attach_logger()
    Tornex.Telemetry.attach_default_logger(ignored: [[:tornex, :bucket, :create]])
    Oban.Telemetry.attach_default_logger(level: :warning, events: ~w(queue notifier peer stager)a)

    children =
      Application.get_env(:tornium, :env)
      |> application_children()

    Supervisor.start_link(children, strategy: :one_for_one, name: Tornium.Supervisor)
  end

  @spec cluster_topology() :: keyword()
  defp cluster_topology() do
    [
      strategy: LibclusterPostgres.Strategy,
      config: [{:channel_name, "tornium_cluster"} | Tornium.Repo.config()]
    ]
  end

  @spec application_children(env :: :test | :dev | :prod) :: [term()]
  defp application_children(env) when env in [:dev, :prod] do
    [
      Tornium.ObanRepo,
      Tornium.Repo,
      {Cluster.Supervisor, [[tornium: cluster_topology()]]},
      Tornium.Telemetry.VerificationLogs,
      Tornium.PromEx,
      {
        Nostrum.Bot,
        %{
          consumer: Tornium.Discord.Consumer,
          intents: [:guilds, :guild_members],
          wrapped_token: fn -> System.get_env("DISCORD_TOKEN") end
        }
      },
      {Tornium.User.KeyStore, name: Tornium.User.KeyStore},
      {Tornium.User.DiscordStore, name: Tornium.User.DiscordStore},
      {Task.Supervisor, name: Tornium.LuaSupervisor},
      {Task.Supervisor, name: Tornium.TornexTaskSupervisor},
      Tornium.API.Supervisor,
      Tornex.HTTP.FinchClient,
      Tornex.NodeRatelimiter,
      Tornex.Scheduler.Supervisor,
      {Oban, Application.fetch_env!(:tornium, Oban)},
      Tornium.Web.Endpoint,
      Tornium.Item.NameCache,
      Tornium.Faction.ChainMonitor.Supervisor
    ]
  end

  defp application_children(:test) do
    [
      Tornium.ObanRepo,
      Tornium.Repo,
      {Cluster.Supervisor, [[tornium: cluster_topology()]]},
      Tornium.Telemetry.VerificationLogs,
      {Tornium.User.KeyStore, name: Tornium.User.KeyStore},
      {Tornium.User.DiscordStore, name: Tornium.User.DiscordStore},
      {Task.Supervisor, name: Tornium.LuaSupervisor},
      {Task.Supervisor, name: Tornium.TornexTaskSupervisor},
      Tornium.API.Supervisor,
      Tornex.HTTP.FinchClient,
      Tornex.NodeRatelimiter,
      Tornex.Scheduler.Supervisor,
      Tornium.Item.NameCache,
      Tornium.Faction.ChainMonitor.Supervisor
    ]
  end
end
