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

if System.get_env("PHX_SERVER") do
  config :tornium, Tornium.Web.Endpoint,
    http: [ip: {127, 0, 0, 1}, port: 4000],
    check_origin: true
end

config :nostrum,
  ffmpeg: nil,
  youtubedl: nil,
  streamlink: nil

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
    pool_size: String.to_integer(System.get_env("POOL_SIZE") || "25"),
    socket_options: maybe_ipv6

  config :tornium, Tornium.ObanRepo,
    url: database_url,
    pool_size: String.to_integer(System.get_env("OBAN_POOL_SIZE") || "10"),
    socket_options: maybe_ipv6
end
