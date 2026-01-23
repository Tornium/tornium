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

config :tornium, Tornium.Repo,
  username: "postgres",
  password: "postgres",
  hostname: "localhost",
  database: "Tornium",
  stacktrace: true,
  show_sensitive_data_on_connection_error: true,
  pool_size: 10

config :tornium, Tornium.ObanRepo,
  username: "postgres",
  password: "postgres",
  hostname: "localhost",
  database: "Tornium",
  stacktrace: true,
  show_sensitive_data_on_connection_error: true,
  pool_size: 10

config :tornium, Tornium.Web.Endpoint,
  http: [ip: {127, 0, 0, 1}, port: 4000],
  check_origin: false,
  debug_errors: true,
  secret_key_base: "XxDP9g/UoipgQSvTqSqFus7TvlSn40KYFVlshlKM7Ey3YsUHjBweDP1r43tsS4Fa"

# Set a higher stacktrace during development. Avoid configuring such
# in production as building large stacktraces may be expensive.
config :phoenix, :stacktrace_depth, 20

# Initialize plugs at runtime for faster development compilation
config :phoenix, :plug_init_mode, :runtime

config :phoenix_live_view,
  # Include HEEx debug annotations as HTML comments in rendered markup
  debug_heex_annotations: true,
  # Enable helpful, but potentially expensive runtime checks
  enable_expensive_runtime_checks: true
