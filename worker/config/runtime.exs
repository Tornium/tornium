import Config

config :nostrum,
  youtubedl: nil,
  streamlink: nil,
  gateway_intents: [
    :guild_members
  ],
  token: System.get_env("DISCORD_TOKEN") || raise "environment variable DISCORD_TOKEN is missing."

if config_env() == :prod do
  database_url =
    System.get_env("DATABASE_URL") ||
      raise """
      environment variable DATABASE_URL is missing.
      For example: ecto://USER:PASS@HOST/DATABASE
      """

  maybe_ipv6 = if System.get_env("ECTO_IPV6") in ~w(true 1), do: [:inet6], else: []

  config :tornium, Tornium.Repo,
    # ssl: true,
    url: database_url,
    pool_size: String.to_integer(System.get_env("POOL_SIZE") || "10"),
    socket_options: maybe_ipv6
end
