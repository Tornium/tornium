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

defmodule Tornium.API.Error do
  @type t :: %__MODULE__{
          code: integer(),
          error: String,
          message: String
        }

  defstruct [
    :code,
    :error,
    :message
  ]

  @spec construct(code :: integer(), error :: String.t()) :: t()
  def construct(code, error) when is_integer(code) do
    case {code, error} do
      {0, _} ->
        %Tornium.API.Error{code: code, error: error, message: "Unhandled error, should not occur."}

      {1, _} ->
        %Tornium.API.Error{code: code, error: error, message: "Private key is empty in current request."}

      {2, _} ->
        %Tornium.API.Error{code: code, error: error, message: "Private key is wrong/incorrect format."}

      {3, _} ->
        %Tornium.API.Error{code: code, error: error, message: "Requesting an incorrect basic type."}

      {4, _} ->
        %Tornium.API.Error{code: code, error: error, message: "Requesting incorrect selection fields."}

      {5, _} ->
        %Tornium.API.Error{
          code: code,
          error: error,
          message:
            "Requests are blocked for a small period of time because of too many requests per user (max 100 per minute)."
        }

      {6, _} ->
        %Tornium.API.Error{code: code, error: error, message: "Wrong ID value."}

      {7, _} ->
        %Tornium.API.Error{
          code: code,
          error: error,
          message: "A requested selection is private (For example, personal data of another user / faction)."
        }

      {8, _} ->
        %Tornium.API.Error{
          code: code,
          error: error,
          message: "Current IP is banned for a small period of time because of abuse."
        }

      {9, _} ->
        %Tornium.API.Error{code: code, error: error, message: "API system is currently disabled."}

      {10, _} ->
        %Tornium.API.Error{
          code: code,
          error: error,
          message: "Current key can't be used because owner is in federal jail."
        }

      {11, _} ->
        %Tornium.API.Error{code: code, error: error, message: "You can only change your API key once every 60 seconds."}

      {12, _} ->
        %Tornium.API.Error{code: code, error: error, message: "Error reading key from database."}

      {13, _} ->
        %Tornium.API.Error{code: code, error: error, message: "The key owner hasn't been online for more than 7 days."}

      {14, _} ->
        %Tornium.API.Error{
          code: code,
          error: error,
          message: "Too many records have been pulled today by this user from our cloud services."
        }

      {15, _} ->
        %Tornium.API.Error{
          code: code,
          error: error,
          message: "An error code specifically for testing purposes that has no dedicated meaning."
        }

      {16, _} ->
        %Tornium.API.Error{
          code: code,
          error: error,
          message: "A selection is being called of which this key does not have permission to access."
        }

      {17, _} ->
        %Tornium.API.Error{code: code, error: error, message: "Backend error occurred, please try again."}

      {18, _} ->
        %Tornium.API.Error{code: code, error: error, message: "API key has been paused by the owner."}

      {19, _} ->
        %Tornium.API.Error{code: code, error: error, message: "The key owner hasn't migrated to crimes 2.0."}

      {20, _} ->
        %Tornium.API.Error{code: code, error: error, message: "This race has not finished yet."}

      {21, _} ->
        %Tornium.API.Error{code: code, error: error, message: "Invalid category value."}
    end
  end
end
