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

defmodule Tornium.Schema.TornEvent do
  @moduledoc """
  An official in-game event or competition.
  """

  use Ecto.Schema
  alias Tornium.Repo

  @type torn_event_type() :: :competition | :event

  @type t :: %__MODULE__{
          guid: Ecto.UUID.t(),
          title: String.t(),
          description: String.t(),
          type: torn_event_type(),
          start_timestamp: DateTime.t(),
          end_timestamp: DateTime.t(),
          configurable: boolean()
        }

  @one_day _seconds = 86_400

  @primary_key {:guid, Ecto.UUID, autogenerate: true}
  schema "torn_event" do
    field(:title, :string)
    field(:description, :string)
    field(:type, Ecto.Enum, values: [:competition, :event])

    field(:start_timestamp, :utc_datetime)
    field(:end_timestamp, :utc_datetime)
    field(:configurable, :boolean)
  end

  @doc """
  Parse a Torn event from the API response.
  """
  @spec parse(
          data :: Torngen.Client.Schema.TornCalendarActivity.t(),
          event_type :: torn_event_type() | nil
        ) :: t()
  def parse(
        %Torngen.Client.Schema.TornCalendarActivity{
          title: title,
          description: description,
          start: start_timestamp,
          end: end_timestamp,
          fixed_start_time: fixed_start_time
        } = _data,
        event_type \\ nil
      ) do
    {normalized_start_timestamp, normalized_end_timestamp} =
      normalize_timestamps(start_timestamp, end_timestamp, fixed_start_time)

    %__MODULE__{
      guid: Ecto.UUID.generate(),
      title: title,
      description: description,
      type: event_type,
      start_timestamp: normalized_start_timestamp,
      end_timestamp: normalized_end_timestamp,
      configurable: not fixed_start_time
    }
  end

  # TEST: Add some tests to validate how this works
  @doc """
  Normalize the start and end timestamps of an event.

  If the event has a fixed start time, the event uses the timestamps reported by the API.

  If the event doesn't have a fixed start time and the event lasts for a day (according to the
  API), the event starts one day prior at the user's start time and ends the next day. If the
  event doesn't have a fixed start time and the event lasts for more than a day (according
  to the API), the event starts on the date specified by the API but at the user's start time
  and ends on the date in the API at the user's start time. For both of these cases when the
  event doesn't have a fixed start time, we will use 1200 TCT as the start time as the
  "median" (even though 1300 TCT is the median).

  Source: https://www.torn.com/forums.php#/p=threads&f=19&t=16516871&b=0&a=0&start=0&to=26704901
  """
  @spec normalize_timestamps(
          start_timestamp :: DateTime.t() | pos_integer(),
          end_timestamp :: DateTime.t() | pos_integer(),
          fixed_start_time? :: boolean()
        ) :: {start_timestamp :: DateTime.t(), end_timestamp :: DateTime.t()}
  def normalize_timestamps(start_timestamp, end_timestamp, fixed_start_time?)
      when is_integer(start_timestamp) and is_integer(end_timestamp) and is_boolean(fixed_start_time?) do
    normalize_timestamps(
      DateTime.from_unix!(start_timestamp),
      DateTime.from_unix!(end_timestamp),
      fixed_start_time?
    )
  end

  def normalize_timestamps(%DateTime{} = start_timestamp, %DateTime{} = end_timestamp, true = _fixed_start_time?) do
    {start_timestamp, end_timestamp}
  end

  def normalize_timestamps(%DateTime{} = start_timestamp, %DateTime{} = end_timestamp, false = _fixed_start_time?) do
    api_event_duration = DateTime.diff(end_timestamp, start_timestamp)
    one_day_event? = api_event_duration <= @one_day

    normalized_start_date = DateTime.to_date(start_timestamp)
    normalized_end_date = DateTime.to_date(end_timestamp)

    {normalized_start_date, normalized_end_date} =
      if one_day_event? do
        {Date.add(normalized_start_date, -1), Date.add(normalized_start_date, 1)}
      else
        {normalized_start_date, normalized_end_date}
      end

    {:ok, normalized_start_timestamp} = DateTime.new(normalized_start_date, ~T[12:00:00], "Etc/UTC")
    {:ok, normalized_end_timestamp} = DateTime.new(normalized_end_date, ~T[12:00:00], "Etc/UTC")

    {normalized_start_timestamp, normalized_end_timestamp}
  end

  @doc """
  Upsert all events from the calendar to the database.
  """
  @spec upsert_all(events :: [t()]) :: {pos_integer(), nil}
  def upsert_all([] = _events) do
    {0, nil}
  end

  def upsert_all([%__MODULE__{} | _] = events) when is_list(events) do
    Repo.insert_all(
      __MODULE__,
      Enum.map(events, &map/1),
      conflict_target: {:unsafe_fragment, "(title, " <> unique_fragment() <> ")"},
      on_conflict: {:replace, [:title, :description, :type, :start_timestamp, :end_timestamp, :configurable]}
    )
  end

  @spec map(event :: t()) :: map()
  defp map(%__MODULE__{} = event) do
    event
    |> Map.from_struct()
    |> Map.drop([:__struct__, :__meta__])
  end

  @doc false
  @spec unique_fragment() :: String.t()
  def unique_fragment(), do: "EXTRACT(YEAR FROM start_timestamp)"
end
