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
    # Attach the default loggers from :telemetry before the start of the children
    Tornex.Telemetry.attach_default_logger()
    Oban.Telemetry.attach_default_logger()

    # TODO: Stop using `Tornium.TornexTaskSupervisor`
    children = [
      Tornium.PromEx,
      Tornium.Repo,
      Tornium.Discord.Consumer,
      {Tornium.User.KeyStore, name: Tornium.User.KeyStore},
      {Task.Supervisor, name: Tornium.LuaSupervisor},
      {Task.Supervisor, name: Tornium.TornexTaskSupervisor},
      Tornium.API.Store,
      Tornex.Scheduler.Supervisor,
      {Oban, Application.fetch_env!(:tornium, Oban)},
      Tornium.Web.Endpoint
    ]

    Supervisor.start_link(children, strategy: :one_for_one, name: Tornium.Supervisor)
  end
end
