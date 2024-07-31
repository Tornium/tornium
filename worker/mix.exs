defmodule Tornium.MixProject do
  use Mix.Project

  def project do
    [
      app: :tornium,
      version: "0.1.0",
      elixir: "~> 1.16",
      start_permanent: Mix.env() == :prod,
      deps: deps()
    ]
  end

  def application do
    [
      mod: {Tornium.Application, []},
      extra_applications: [:logger]
    ]
  end

  def deps do
    [
      {:ecto, "~> 3.0"},
      {:ecto_sql, "~> 3.10"},
      {:nostrum, "~> 0.10"},
      {:postgrex, ">= 0.0.0"},
    ]
  end
end
