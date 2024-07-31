defmodule Tornium.MixProject do
  use Mix.Project

  @version "0.1.0"

  def project do
    [
      app: :tornium,
      version: @version,
      elixir: "~> 1.16",
      package: package(),
      deps: deps()
    ]
  end

  def application do
    [
      extra_applications: [:logger]
    ]
  end

  def deps do
    [
      {:nostrum, "~> 0.10"}
    ]
  end

  def package do
    [
      description: "Tornium's Elixir Oban and Nostrum worker",
      files: ["lib", "mix.exs"],
      maintainers: ["tiksan"],
      licenses: ["AGPL"],
      links: %{"Github" => "https://github.com/Tornium/tornium/tree/master/worker"}
    ]
  end
end
