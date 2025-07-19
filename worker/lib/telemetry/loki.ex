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

defmodule Tornium.Telemetry.Loki do
  @moduledoc false

  def filter(%{} = log_event, _opts) do
    event_source =
      log_event
      |> Map.get(:meta, %{})
      |> Map.get(:event_source, nil)

    case event_source do
      :telemetry ->
        %{log_event | meta: Map.drop(log_event.meta, [:event_source, :line, :file, :domain, :mfa])}

      _ ->
        :stop
    end
  end

  def ignore_filter(%{} = log_event, _opts) do
    event_source =
      log_event
      |> Map.get(:meta, %{})
      |> Map.get(:event_source, nil)

    case event_source do
      :telemetry ->
        %{log_event | meta: Map.delete(log_event.meta, :event_source)}

      _ ->
        :ignore
    end
  end
end
