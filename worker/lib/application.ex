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
  require Logger
  use Application

  @spec(
    start(Application.start_type(), term()) :: {:ok, pid()},
    {:ok, pid(), Application.state()} | {:error, term()}
  )
  def start(_type, _args) do
    Logger.add_handlers(:tornium)

    # Attach the default loggers from :telemetry before the start of the children
    Tornium.Telemetry.attach_default_logger()
    Tornex.Telemetry.attach_default_logger(ignored: [[:tornex, :bucket, :create]])

    if Application.get_env(:tornium, :env) == :dev do
      Oban.Telemetry.attach_default_logger()
    else
      Oban.Telemetry.attach_default_logger(level: :warning, events: ~w(queue notifier peer stager)a)
    end

    # TODO: Stop using `Tornium.TornexTaskSupervisor`
    children = [
      Tornium.PromEx,
      Tornium.Repo,
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
      Tornium.API.Store,
      Tornex.HTTP.FinchClient,
      Tornex.Scheduler.Supervisor,
      {Oban, Application.fetch_env!(:tornium, Oban)},
      Tornium.Web.Endpoint
    ]

    Supervisor.start_link(children, strategy: :one_for_one, name: Tornium.Supervisor)
  end
end
