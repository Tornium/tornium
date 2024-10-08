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

defmodule Tornium.Trigger do
  alias Tornium.Repo
  import Ecto.Query

  @api_call_priority 10

  @spec execute(trigger :: Tornium.Schema.Trigger.t(), api_key :: Tornium.Schema.TornKey.t()) ::
          {:ok, List} | {:error, any()} | {:lua_error, any()}
  def execute(%Tornium.Schema.Trigger{} = trigger, %Tornium.Schema.TornKey{} = api_key)
      when trigger.resource == :user do
    # TODO: Document this function
    update_next_execution(trigger)

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
      %{"error" => %{"code" => code, "error" => error}} ->
        {:error, Tornium.API.Error.construct(code, error)}

      %{} ->
        # TODO: Handle errors from `Tornium.Lua.execute_lua`
        Tornium.Lua.execute_lua(trigger.code, user: response)
    end
  end

  def execute(%Tornium.Schema.Trigger{} = _trigger) do
    {:error, :not_implemented}
  end

  @spec parse_next_execution(trigger :: Tornium.Schema.Trigger.t()) :: DateTime.t()
  defp parse_next_execution(%Tornium.Schema.Trigger{} = trigger) do
    # TODO: Document this function
    Crontab.CronExpression.Parser.parse!(trigger.cron)
    |> Crontab.Scheduler.get_next_run_date!()
    |> DateTime.from_naive!("Etc/UTC")
  end

  @spec update_next_execution(trigger :: Tornium.Schema.Trigger.t()) :: nil
  def update_next_execution(%Tornium.Schema.Trigger{} = trigger) do
    # TODO: Document this function
    {1, _} =
      Tornium.Schema.Trigger
      |> where(tid: ^trigger.tid)
      |> update(set: [next_execution: ^parse_next_execution(trigger.cron)])
      |> Repo.update_all([])

    nil
  end
end
