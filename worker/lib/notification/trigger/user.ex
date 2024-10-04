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

defmodule Tornex.Trigger do
  @api_call_priority 10

  @spec execute(trigger :: Tornium.Schema.Trigger.t(), api_key :: Tornium.Schema.TornKey.t()) ::
          {:ok, any()} | {:error, atom()}
  def execute(%Tornium.Schema.Trigger{} = trigger, %Tornium.Schema.TornKey{} = api_key)
      when trigger.resource == :user do
    # TODO: Document this function

    response =
      Tornex.Scheduler.Bucket.enqueue(%Tornex.Query{
        resource: "user",
        resource_id: trigger.resource_id,
        selections: trigger.selections,
        key: api_key.api_key,
        key_owner: api_key.user_id,
        nice: @api_call_priority
      })

    case response do
      %{"error" => %{"code" => code, "error" => error}} -> {:error, Tornium.API.Error.construct(code, error)}
      %{} -> nil
    end
  end

  def execute(%Tornium.Schema.Trigger{} = _trigger) do
    {:error, :not_implemented}
  end
end
