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

defmodule Tornium.Faction.ChainMonitor.State do
  @moduledoc """
  State for the `Tornium.Faction.ChainMonitor` GenServer.
  """

  defstruct [:chain_id, :faction_id, :last_updated, :chain_length, :last_attack, :timer_ref]

  @type t() :: %__MODULE__{
          chain_id: pos_integer() | nil,
          faction_id: pos_integer(),
          last_updated: DateTime.t() | nil,
          chain_length: pos_integer() | nil,
          last_attack: DateTime.t() | nil,
          timer_ref: term() | nil
        }

  @doc """
  Convert a keyword list of options to a state struct.

  ## Options
    * `:chain_id` - The Torn ID of the current chain of the faction (default: `nil`)
    * `:faction_id` - The Torn ID of the faction the ChainMonitor will be started against (required) 

  ## Examples

    iex> from_opts!(chain_id: 1, faction_id: 1)
    %Tornium.Faction.ChainMonitor.State{chain_id: 1, faction_id: 1)
  """
  @spec from_opts!(opts :: keyword()) :: t()
  def from_opts!(opts \\ []) do
    %__MODULE__{
      chain_id: Keyword.get(opts, :chain_id, nil),
      faction_id: Keyword.fetch!(opts, :faction_id),
      last_updated: nil,
      chain_length: nil,
      last_attack: nil,
      timer_ref: nil
    }
  end

  # TODO: add an integration test for this
  @doc """
  Convert the chain data from the APIv2 `faction/chain` endpoint to a state struct.
  """
  @spec from_data!(chain_data :: map(), opts :: keyword()) :: t()
  def from_data!(
        %{
          Torngen.Client.Path.Faction.Id.Chain => %{
            FactionOngoingChainResponse => %Torngen.Client.Schema.FactionOngoingChainResponse{
              chain: %Torngen.Client.Schema.FactionOngoingChain{
                id: chain_id,
                current: chain_current,
                end: chain_end,
                timeout: chain_timeout
              }
            }
          }
        },
        opts \\ []
      ) do
    %__MODULE__{
      chain_id: chain_id,
      faction_id: Keyword.fetch!(opts, :faction_id),
      last_updated: DateTime.utc_now(),
      chain_length: chain_current,
      last_attack: DateTime.from_unix!(chain_end - chain_timeout),
      timer_ref: Keyword.get(opts, :timer_ref)
    }
  end

  @doc """
  Set a new timer to update the `Tornium.Faction.ChainMonitor` with new data from a new API call.

  If there is an existing timer that has not been triggered/finished running yet, that timer will
  be cancelled before a new timer is created.
  """
  @spec set_timer(state :: t()) :: t()
  def set_timer(%__MODULE__{last_updated: nil} = state) do
    # When the last updated timestamp is nil, we want to update the data as soon as possible.
    # This state shouldn't be possible though as the last updated timestamp would be set on the
    # initial GenServer instructions.
    send(self(), :check)

    cancel_existing_timer(state)
  end

  def set_timer(%__MODULE__{chain_length: nil} = state) do
    # If the GenServer's state has been updated but the chain hasn't started yet, we should wait
    # for a while to check if the chain has started. We can conservatively let this be 5 minutes.
    ref = Process.send_after(self(), :check, 5 * 60 * 1000)

    state
    |> cancel_existing_timer()
    |> Map.put(:timer_ref, ref)
  end

  def set_timer(%__MODULE__{chain_length: chain_length} = state) when chain_length < 100 do
    # When the chain is not that long, let us say less than 100 long, we shouldn't check that
    # frequently as the chain shouldn't drop and it's likely not a real chain. We can
    # conservatively check this after 5 minutes
    ref = Process.send_after(self(), :check, 5 * 60 * 1000)

    state
    |> cancel_existing_timer()
    |> Map.put(:timer_ref, ref)
  end

  def set_timer(%__MODULE__{last_attack: last_attack} = state) do
    # The chain is in a position where we need to reguarly check in on the chain depending on
    # when the chain was last updated and the last time a hit was made. The closer to when the
    # last known hit was made, the more frequently we should check in on the chain.
    seconds_since = DateTime.diff(DateTime.utc_now(), last_attack, :second)
    seconds_left = 300 - seconds_since

    poll_in =
      cond do
        seconds_left <= 0 ->
          # The chain has died. We should immediately check so that the ChainMonitor can
          # transition to the end state.
          0

        seconds_left >= 90 ->
          # When the time left >= 90, we want to try to get it to check around 90 seconds
          # left.
          seconds_left - 90

        true ->
          # When the time left < 120, we want to repeatedly check in smaller intervals.
          :math.pow(seconds_left, 0.75)
      end
      |> round()
      |> max(5)
      |> Kernel.*(1_000)

    ref = Process.send_after(self(), :check, poll_in)

    state
    |> cancel_existing_timer()
    |> Map.put(:timer_ref, ref)
  end

  @spec cancel_existing_timer(state :: t()) :: t()
  defp cancel_existing_timer(%__MODULE__{timer_ref: ref} = state) when is_nil(ref) do
    state
  end

  defp cancel_existing_timer(%__MODULE__{timer_ref: ref} = state) do
    Process.cancel_timer(ref)

    %{state | timer_ref: nil}
  end
end
