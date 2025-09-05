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

defmodule Tornium.Workers.OAuthRevocation do
  @moduledoc """
  Revoke OAuth access tokens once they have expired.

  The token's `access_token_revoked_at` will be set to the current timestamp. However the
  `refresh_token_revoked_at` value will not be set as the refresh token will be required to replace an expired
  access token. The refresh token can be revoked when it expires (according to a policy to be determined), when
  the application is deleted, etc.
  """

  require Logger
  alias Tornium.Repo
  import Ecto.Query

  use Oban.Worker,
    max_attempts: 5,
    priority: 0,
    queue: :scheduler,
    tags: ["scheduler", "user"],
    unique: [
      period: :infinity,
      fields: [:worker],
      states: :incomplete
    ]

  @impl Oban.Worker
  def perform(%Oban.Job{} = _job) do
    Tornium.Schema.OAuthToken
    |> where([t], is_nil(t.access_token_revoked_at))
    |> where([t], ^DateTime.utc_now() > datetime_add(t.issued_at, t.expires_in, "second"))
    |> update([t], set: [access_token_revoked_at: ^DateTime.utc_now()])
    |> Repo.update_all([])

    :ok
  end
end
