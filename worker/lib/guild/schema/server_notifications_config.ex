# Copyright (C) 2021-2023 tiksan
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

defmodule Tornium.Schema.ServerNotificationsConfig do
  use Ecto.Schema

  @type t :: %__MODULE__{
          id: integer(),
          server: Tornium.Schema.Server.t(),
          enabled: boolean(),
          log_channel: integer()
        }

  @primary_key {:id, :id, autogenerate: true}
  # schema "server_notifications_config" do
  schema "servernotificationsconfig" do
    belongs_to(:server, Tornium.Schema.Server, references: :sid)

    field(:enabled, :boolean)
    field(:log_channel, :integer)
  end
end
