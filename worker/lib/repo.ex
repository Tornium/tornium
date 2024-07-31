defmodule Tornium.Repo do
  use Ecto.Repo,
    otp_app: :tornium,
    adapter: Ecto.Adapters.Postgres
end
