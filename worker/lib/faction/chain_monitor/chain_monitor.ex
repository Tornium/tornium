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

defmodule Tornium.Faction.ChainMonitor do
  @moduledoc """
  Monitor a specific faction's chain for the duration of the chain.

  When the GenServer first starts for a chain, we will want to check if should be enabled. The ChainMonitor
  should only be enabled if any of the features used for the ChainMonitor are enabled. If should be enabled,
  we will want to send a messaage to the chain timeout channel indicating that the ChainMonitor has started
  for that faction's chain.

  Typically, while the ChainMonitor is running, the chain monitor will make an API call at some frequency
  dependent upon the time left in the chain and the hit count of the chain. If the time left in the chain
  is low, we should increase the API call frequency to ensure notifications are sent to keep the chain alive.
  """

  use GenServer
  import Ecto.Query
  alias Tornium.Repo

  @doc """
  Start a ChainMonitor for a specific faction.

  For the ChainMonitor to start, the faction must have a linked Discord server and a configured chain alert
  channel in the `Tornium.Schema.ServerAttackConfig` for the server + faction. Otherwise,
  `{:error, "Invalid configuration"}` will be returned.

  ## Options
    * `:faction_id` - The Torn ID of the faction the ChainMonitor will be started against (required)
  """
  @spec start_link(opts :: keyword()) :: GenServer.on_start()
  def start_link(opts \\ []) do
    faction_id = Keyword.fetch!(opts, :faction_id)

    # We should check if the faction is configured properly here and not start the server if it isn't.
    case Tornium.Schema.ServerAttackConfig.config(faction_id) do
      nil ->
        {:error, "Missing configuration"}

      %Tornium.Schema.ServerAttackConfig{chain_alert_channel: chain_alert_channel}
      when is_integer(chain_alert_channel) and chain_alert_channel > 0 ->
        GenServer.start_link(__MODULE__, opts,
          name: {:via, Registry, {Tornium.Faction.ChainMonitor.Registry, faction_id}}
        )

      %Tornium.Schema.ServerAttackConfig{} ->
        {:error, "Invalid configuration"}
    end
  end

  @doc """
  Execute the check of the chain monitor for a specific faction.

  ## Options
    * `:faction_id` - The Torn ID of the faction the ChainMonitor will be started against (required) 
    * `:timeout` - The timeout in milliseconds (default: `5_000`).
  """
  @spec check(opts :: keyword()) :: :ok
  def check(opts \\ []) do
    faction_id = Keyword.fetch!(opts, :faction_id)
    timeout = Keyword.get(opts, :timeout, 5_000)

    GenServer.call({:via, Registry, {Tornium.Faction.ChainMonitor.Registry, faction_id}}, :check, timeout)
  end

  @impl true
  def init(opts \\ []) do
    {:ok, Tornium.Faction.ChainMonitor.State.from_opts!(opts), {:continue, :initial}}
  end

  @impl true
  def handle_continue(:initial, %Tornium.Faction.ChainMonitor.State{faction_id: faction_id} = state) do
    case query(state) do
      nil ->
        # There was no initial API key to use for this ChainMonitor.
        send_message(faction_id, %Nostrum.Struct.Message{
          embeds: [
            %Nostrum.Struct.Embed{
              title: "ChainMonitor Error",
              description:
                "The ChainMonitor for faction ID #{faction_id} has been disabled as no API keys could be found to use for the feature.",
              color: Tornium.Discord.Constants.colors()[:error]
            }
          ]
        })

        disable(faction_id, reason: "No AA API keys found")
        {:stop, "Stopped ChainMonitor as no API key was found for faction #{faction_id}"}

      %Tornex.SpecQuery{} = initial_query ->
        chain_data = Tornex.Scheduler.Bucket.enqueue(initial_query)
        parsed_chain_data = Tornex.SpecQuery.parse(initial_query, chain_data)

        {
          :noreply,
          Tornium.Faction.ChainMonitor.State.from_data!(parsed_chain_data, faction_id: faction_id),
          {:continue, :initial_message}
        }
    end
  end

  @impl true
  def handle_continue(
        :initial_message,
        %Tornium.Faction.ChainMonitor.State{faction_id: faction_id, chain_length: chain_length} = state
      )
      when is_integer(chain_length) and chain_length == 0 do
    faction_id
    |> send_message(%Nostrum.Struct.Message{
      content: "ChainMonitor has started for faction ID #{faction_id} and is waiting on the first hit."
    })
    |> try_timer(state)
  end

  @impl true
  def handle_continue(
        :initial_message,
        %Tornium.Faction.ChainMonitor.State{faction_id: faction_id, chain_length: chain_length} = state
      )
      when is_integer(chain_length) and chain_length > 0 do
    faction_id
    |> send_message(%Nostrum.Struct.Message{
      content: "ChainMonitor has started for faction ID #{faction_id} at chain ##{Tornium.Utils.commas(chain_length)}."
    })
    |> try_timer(state)
  end

  @impl true
  def handle_continue(:message, %Tornium.Faction.ChainMonitor.State{chain_length: chain_length} = state)
      when is_integer(chain_length) and chain_length < 100 do
    # Since the chain is below 100 hits, we can ignore the chain timer and not send any messages for it.
    try_timer({:ok, nil}, state)
  end

  @impl true
  def handle_continue(
        :message,
        %Tornium.Faction.ChainMonitor.State{
          faction_id: faction_id,
          last_attack: last_attack,
          chain_length: chain_length
        } = state
      ) do
    seconds_since = DateTime.diff(DateTime.utc_now(), last_attack, :second)
    seconds_left = 300 - seconds_since

    # If the seconds left on the chain is less thn the configured minimum chain duration, we'll need to send
    # a message. Otherwise, we should start the timer for the next check of the chain timer.
    case Tornium.Schema.ServerAttackConfig.config(faction_id) do
      %Tornium.Schema.ServerAttackConfig{chain_alert_channel: chain_alert_channel}
      when not is_integer(chain_alert_channel) or chain_alert_channel <= 0 ->
        {:stop, "Stopped ChainMonitor as the feature was disabled for faction #{faction_id}"}

      _ when seconds_left <= 0 ->
        # When the chain timer is 0, we should stop the ChainMonitor to reduce resource usage.
        send_message(faction_id, %Nostrum.Struct.Message{
          content:
            "ChainMonitor has stopped for faction ID #{faction_id} as the chain has ended at chain ##{Tornium.Utils.commas(chain_length)}."
        })

        {:stop, "Stopped ChainMonitor as chain has ended for faction #{faction_id}"}

      %Tornium.Schema.ServerAttackConfig{chain_alert_minimum: chain_alert_minimum}
      when seconds_left <= chain_alert_minimum ->
        # Since there are fewer seconds left on the chain than the configured minimum, we should try to send
        # an notifiction for this.
        # TODO: Add the role ping to this
        faction_id
        |> send_message(%Nostrum.Struct.Message{
          content: "Chain Alert!!!",
          embeds: [
            %Nostrum.Struct.Embed{
              title: "Chain Timer Alert",
              description:
                "The chain timer for {faction.name} [#{faction_id}] will reach zero <t:#{DateTime.to_unix(last_attack) + 300}:R> with a current chain length of #{Tornium.Utils.commas(chain_length)}.",
              color: Tornium.Discord.Constants.colors()[:error]
            }
          ]
        })
        |> try_timer(state)

      %Tornium.Schema.ServerAttackConfig{} ->
        # Since the chain timer was higher than the configured minimum, we can just restart the timer of
        # the ChainMonitor for the faction.
        try_timer({:ok, nil}, state)

      nil ->
        # Since there is no configuration found for the faction, we can stop the ChainMonitor for the faction.
        disable(faction_id, reason: "No configuration found")
        {:stop, "Stopped ChainMonitor as no configuration was found for faction #{faction_id}"}
    end
  end

  @impl true
  def handle_call(
        :check,
        _from,
        %Tornium.Faction.ChainMonitor.State{faction_id: faction_id, timer_ref: timer_ref} = state
      ) do
    case query(state) do
      nil ->
        # There was no API key available to use for this ChainMonitor so we should stop it
        send_message(faction_id, %Nostrum.Struct.Message{
          embeds: [
            %Nostrum.Struct.Embed{
              title: "ChainMonitor Error",
              description:
                "The ChainMonitor for faction ID #{faction_id} has been disabled as no API keys could be found to use for the feature.",
              color: Tornium.Discord.Constants.colors()[:error]
            }
          ]
        })

        disable(faction_id, reason: "No AA API keys found")
        {:stop, "Stopped ChainMonitor as no API key was found for faction #{faction_id}"}

      %Tornex.SpecQuery{} = chain_query ->
        chain_data = Tornex.Scheduler.Bucket.enqueue(chain_query)
        parsed_chain_data = Tornex.SpecQuery.parse(chain_query, chain_data)

        {
          :reply,
          :ok,
          Tornium.Faction.ChainMonitor.State.from_data!(parsed_chain_data, faction_id: faction_id, timer_ref: timer_ref),
          {:continue, :message}
        }
    end
  end

  @impl true
  def handle_info(:check, %Tornium.Faction.ChainMonitor.State{faction_id: faction_id, timer_ref: timer_ref} = state) do
    case query(state) do
      nil ->
        # There was no API key available to use for this ChainMonitor so we should stop it
        send_message(faction_id, %Nostrum.Struct.Message{
          embeds: [
            %Nostrum.Struct.Embed{
              title: "ChainMonitor Error",
              description:
                "The ChainMonitor for faction ID #{faction_id} has been disabled as no API keys could be found to use for the feature.",
              color: Tornium.Discord.Constants.colors()[:error]
            }
          ]
        })

        disable(faction_id, reason: "No AA API keys found")
        {:stop, "Stopped ChainMonitor as no API key was found for faction #{faction_id}"}

      %Tornex.SpecQuery{} = chain_query ->
        chain_data = Tornex.Scheduler.Bucket.enqueue(chain_query)
        parsed_chain_data = Tornex.SpecQuery.parse(chain_query, chain_data)

        {
          :noreply,
          Tornium.Faction.ChainMonitor.State.from_data!(parsed_chain_data, faction_id: faction_id, timer_ref: timer_ref),
          {:continue, :message}
        }
    end
  end

  @spec try_timer(
          message_response :: Nostrum.Api.error() | {:ok, Nostrum.Struct.Message.t() | term()},
          state :: Tornium.Faction.ChainMonitor.State.t()
        ) ::
          {:noreply, Tornium.Faction.ChainMonitor.State.t()}
          | {:stop, reason :: term(), Tornium.Faction.ChainMonitor.State.t()}
  defp try_timer(
         {:error, %Nostrum.Error.ApiError{response: %{code: discord_error_code, message: discord_error_message}}} =
           _message_response,
         %Tornium.Faction.ChainMonitor.State{faction_id: faction_id} = _state
       )
       when discord_error_code in [
              # Unknown channel
              10_003,
              # Cannot send a message in a forum channel
              40_058,
              # Missing access
              50_001,
              # Cannot send an empty message
              50_006,
              # Cannot send messages to this user
              50_007,
              # Cannot send messages in a non-text channel
              50_008
            ] do
    # Since there was some sort of error from the Discord API, we should stop the ChainMonitor if the error
    # code indicates that no message could be sent.
    disable(faction_id, reason: "Discord error #{discord_error_code} (#{discord_error_message})")
    {:stop, "Stopped ChainMonitor as Discord errored code #{discord_error_code} for faction #{faction_id}"}
  end

  defp try_timer({:error, %Nostrum.Error.ApiError{}} = _message_response, %Tornium.Faction.ChainMonitor.State{} = state) do
    # As ths error code hasn't been caught above, we can assume ths error to be some sort of transient error that
    # may go away the next iteration of the timer's execution.
    {:noreply, Tornium.Faction.ChainMonitor.State.set_timer(state)}
  end

  defp try_timer({:ok, _} = _message_response, %Tornium.Faction.ChainMonitor.State{} = state) do
    # Since the message was succesfully sent, we can set a new timer for the chain monitor.
    {:noreply, Tornium.Faction.ChainMonitor.State.set_timer(state)}
  end

  @spec query(state :: Tornium.Faction.ChainMonitor.State.t()) :: Tornex.SpecQuery.t() | nil
  defp query(%Tornium.Faction.ChainMonitor.State{faction_id: faction_id} = _state) do
    case Tornium.Faction.get_key(faction_id) do
      %Tornium.Schema.TornKey{api_key: api_key, user_id: api_key_owner} ->
        # Since monitoring the chain is typically extremely high priority to prevent chain drops, we should use
        # the maximum priority of -20.
        Tornex.SpecQuery.new(nice: -20)
        |> Tornex.SpecQuery.put_path(Torngen.Client.Path.Faction.Id.Chain)
        |> Tornex.SpecQuery.put_parameter!(:id, faction_id)
        |> Tornex.SpecQuery.put_key(api_key)
        |> Tornex.SpecQuery.put_key_owner(api_key_owner)

      nil ->
        nil
    end
  end

  if Application.compile_env!(:tornium, :env) == :test do
    defp send_message(_faction_id, message) do
      {:ok, message}
    end
  end

  @spec send_message(faction_id :: pos_integer(), message :: Nostrum.Struct.Message.t()) ::
          Nostrum.Api.error() | {:ok, Nostrum.Struct.Message.t()}
  defp send_message(faction_id, %Nostrum.Struct.Message{} = message) when is_integer(faction_id) do
    faction_id
    |> Tornium.Schema.ServerAttackConfig.config()
    |> send_message(message)
  end

  @spec send_message(faction_config :: Tornium.Schema.ServerAttackConfig.t(), message :: Nostrum.Struct.Message.t()) ::
          Nostrum.Api.error() | {:ok, Nostrum.Struct.Message.t()}
  defp send_message(
         %Tornium.Schema.ServerAttackConfig{chain_alert_channel: chain_alert_channel} = _faction_config,
         %Nostrum.Struct.Message{} = message
       )
       when not is_nil(chain_alert_channel) and chain_alert_channel != 0 do
    Nostrum.Api.Message.create(
      chain_alert_channel,
      message
      |> Map.from_struct()
      |> Map.to_list()
    )
  end

  @doc """
  Disable the chain monitor feature for a specific faction.

  ## Options
    * `:reason` - The reason for disabling the feature (default: `nil`).
  """
  @spec disable(faction_id :: pos_integer(), opts :: keyword()) :: term()
  def disable(faction_id, _opts \\ []) when is_integer(faction_id) do
    Tornium.Schema.ServerAttackConfig
    |> where([c], c.faction_id == ^faction_id)
    |> join(:inner, [c], f in assoc(c, :faction), on: c.faction_id == f.tid)
    |> join(:inner, [c, f], s in assoc(f, :guild), on: f.guild_id == s.sid)
    |> where([c, f, s], ^faction_id in s.factions)
    |> update(set: [chain_alert_channel: nil])
    |> Repo.update_all([])

    # TODO: Log this to the alloy log file
  end
end
