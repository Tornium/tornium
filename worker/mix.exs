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

defmodule Tornium.MixProject do
  use Mix.Project

  def project do
    [
      app: :tornium,
      version: "0.1.0",
      elixir: "~> 1.16",
      start_permanent: Mix.env() == :prod,
      deps: deps(),
      elixirc_paths: elixirc_paths(Mix.env()),
      aliases: aliases()
    ]
  end

  def application do
    [
      mod: {Tornium.Application, []},
      extra_applications: [:logger, :plug_cowboy, :runtime_tools]
    ]
  end

  def deps do
    [
      # Nostrum >= 0.9.0-rc1 requires certifi ~> 2.13 and hackney >= 1.18.2 requires certifi ~> 2.12
      {:certifi, "~> 2.13", override: true},
      {:ecto, "~> 3.0"},
      {:ecto_sql, "~> 3.10"},
      {:nostrum, "~> 0.10"},
      {:postgrex, ">= 0.0.0"},
      {:prom_ex, "~> 1.10"},
      {:crontab, "~> 1.1"},
      {:oban, "~> 2.19"},
      # Required for oban_web
      {:plug_cowboy, "~> 2.7"},
      {:oban_web, "~> 2.11"},
      {:bandit, "~> 1.2"},
      {:luerl, github: "rvirding/luerl", tag: "1.2.3"},
      {:solid, "~> 0.17.2"},
      {:tornex, git: "https://github.com/Tornium/tornex.git", ref: "db81d670226badff4d09807e51cc0f7f63bbdf8b"}
    ]
  end

  defp aliases do
    [
      "ecto.setup": ["ecto.create", "ecto.migrate"],
      "ecto.reset": ["ecto.drop", "ecto.setup"],
      test: ["ecto.drop", "ecto.create", "ecto.migrate", "test", "ecto.drop"]
    ]
  end

  defp elixirc_paths(:test), do: ["lib", "test"]
  defp elixirc_paths(_), do: ["lib"]
end
