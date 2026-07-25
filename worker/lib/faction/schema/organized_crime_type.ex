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

defmodule Tornium.Schema.OrganizedCrimeType do
  @moduledoc """
  Data on each type of Organized Crime.
  """

  use Ecto.Schema
  alias Tornium.Repo

  @typedoc """
  Name of each spawn level spawning the following difficulty levels:

  Lambda (1): 1 -- 2
  Sigma (2): 3 --4 
  Phi (3): 5 -- 6
  Psi (4): 7 -- 8
  Omega (5): Elaborate 8 -- 10
  """
  @type spawn_level() :: :lambda | :sigma | :phi | :psi | :omega

  @type t :: %__MODULE__{
          guid: Ecto.UUID.t(),
          name: String.t(),
          description: String.t(),
          difficulty: 1..9,
          spawn_level: spawn_level(),
          prerequisite_id: Ecto.UUID.t() | nil,
          prerequisite: Tornium.Schema.OrganizedCrime.t() | nil,
          slots: [Tornium.Schema.OrganizedCrimeSlotType.t()] | nil
        }

  @primary_key {:guid, Ecto.UUID, autogenerate: true}
  schema "organized_crime_type" do
    field(:name, :string)
    field(:description, :string)
    field(:difficulty, :integer)
    field(:spawn_level, Ecto.Enum, values: [lambda: 1, sigma: 2, phi: 3, psi: 4, omega: 5])
    belongs_to(:prerequisite, __MODULE__, references: :guid, type: Ecto.UUID)

    has_many(:slots, Tornium.Schema.OrganizedCrimeSlotType, foreign_key: :oc_type_id)
  end

  @doc """
  Parse the API response into the schema struct.

  If the full response (`TornOrganizedCrimeResponse`) is provided, a list of the schema
  struct will be provided. If it's only a single `TornOrganizedCrime`, a single schema struct
  will be returned.

  The `:prerequisite_id` will always be set to `nil` by this function as the primary key of
  the prerequisite is required to fill that.
  """
  @spec from_data!(
          data :: Torngen.Client.Schema.TornOrganizedCrimeResponse.t() | Torngen.Client.Schema.TornOrganizedCrime.t()
        ) :: t() | [t()]
  def from_data!(%Torngen.Client.Schema.TornOrganizedCrimeResponse{organizedcrimes: crimes} = _data) do
    Enum.map(crimes, &from_data!/1)
  end

  def from_data!(
        %Torngen.Client.Schema.TornOrganizedCrime{
          spawn: %Torngen.Client.Schema.TornOrganizedCrimeSpawn{
            level: spawn_level
          },
          name: name,
          difficulty: difficulty,
          description: description
        } = _data
      ) do
    %__MODULE__{
      guid: Ecto.UUID.generate(),
      name: name,
      description: description,
      difficulty: difficulty,
      spawn_level: map_spawn_level!(spawn_level),
      prerequisite_id: nil
    }
  end

  # TODO: Add doc
  # TEST: Add test
  @spec upsert_all!(data :: Torngen.Client.Schema.TornOrganizedCrimeResponse.t()) :: :ok
  def upsert_all!(%Torngen.Client.Schema.TornOrganizedCrimeResponse{} = data) do
    {_, crime_types} =
      Repo.insert_all(
        __MODULE__,
        data
        |> from_data!()
        |> Enum.map(fn crime_type ->
          crime_type
          |> Map.from_struct()
          |> Map.drop([:__struct__, :__meta__, :slots, :prerequisite])
        end),
        returning: true,
        conflict_target: :name,
        on_conflict: {:replace, [:description, :difficulty, :spawn_level]}
      )

    mapped_prerequisities = map_prerequisite_ocs(data)

    crime_types_with_prerequisities =
      Enum.reduce(crime_types, [], fn %__MODULE__{name: name} = crime_type, acc ->
        crime_prerequisite_name = Map.get(mapped_prerequisities, name)

        crime_prerequisite_id =
          case Enum.find(crime_types, &(&1.name == crime_prerequisite_name)) do
            %__MODULE__{guid: crime_type_guid} -> crime_type_guid |> Ecto.UUID.cast!()
            _ -> nil
          end

        [
          %__MODULE__{crime_type | prerequisite_id: crime_prerequisite_id}
          |> Map.from_struct()
          |> Map.drop([:__struct__, :__meta__, :slots, :prerequisite])
          | acc
        ]
      end)

    {_, crime_types} =
      Repo.insert_all(__MODULE__, crime_types_with_prerequisities,
        returning: true,
        conflict_target: :name,
        on_conflict: {:replace, [:prerequisite_id]}
      )

    Tornium.Schema.OrganizedCrimeSlotType.upsert_all!(data, crime_types)

    :ok
  end

  @doc """
  Map the integer spawn level to the atom.

  ## Examples

    iex> map_spawn_level!(2)
    :sigma
  """
  @spec map_spawn_level!(spawn_level_number :: integer()) :: spawn_level()
  def map_spawn_level!(spawn_level_number) when is_integer(spawn_level_number) do
    case spawn_level_number do
      1 -> :lambda
      2 -> :sigma
      3 -> :phi
      4 -> :psi
      5 -> :omega
    end
  end

  @spec from_data!(data :: Torngen.Client.Schema.TornOrganizedCrimeResponse.t()) :: %{String.t() => String.t()}
  defp map_prerequisite_ocs(%Torngen.Client.Schema.TornOrganizedCrimeResponse{organizedcrimes: crimes} = _data) do
    crimes
    |> Enum.map(&do_map_prerequisite_ocs/1)
    |> Enum.reject(&is_nil/1)
    |> Map.new()
  end

  defp do_map_prerequisite_ocs(%Torngen.Client.Schema.TornOrganizedCrime{prerequisite: prerequisite} = _data)
       when is_nil(prerequisite) do
    nil
  end

  defp do_map_prerequisite_ocs(
         %Torngen.Client.Schema.TornOrganizedCrime{name: name, prerequisite: prerequisite_name} = _data
       ) do
    {name, prerequisite_name}
  end
end
