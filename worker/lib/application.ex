defmodule Tornium.Application do
  require Logger
  use Application

  @spec start(Application.start_type(), term()) :: {:ok, pid()}, {:ok, pid(), Application.state()} | {:error, term()}
  def start(_type, _args) do
    children = [
      Tornium.Repo,
      Tornium.Discord.Consumer
    ]

    Supervisor.start_link(children, strategy: :one_for_one, name: Tornium.Supervisor)
  end
end
