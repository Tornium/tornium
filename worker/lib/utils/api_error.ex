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
          code: 0..24,
          error: String.t(),
          message: String.t()
        }

  defstruct [
    :code,
    :error,
    :message
  ]

  @spec construct(code :: 0..24, error :: String.t()) :: t()
  def construct(0, error) when is_binary(error) do
    %Tornium.API.Error{code: 0, error: error, message: "Unhandled error, should not occur."}
  end

  def construct(1, error) when is_binary(error) do
    %Tornium.API.Error{code: 1, error: error, message: "Private key is empty in current request."}
  end

  def construct(2, error) when is_binary(error) do
    %Tornium.API.Error{code: 2, error: error, message: "Private key is wrong/incorrect format."}
  end

  def construct(3, error) when is_binary(error) do
    %Tornium.API.Error{code: 3, error: error, message: "Requesting an incorrect basic type."}
  end

  def construct(4, error) when is_binary(error) do
    %Tornium.API.Error{code: 4, error: error, message: "Requesting incorrect selection fields."}
  end

  def construct(5, error) when is_binary(error) do
    %Tornium.API.Error{
      code: 5,
      error: error,
      message:
        "Requests are blocked for a small period of time because of too many requests per user (max 100 per minute)."
    }
  end

  def construct(6, error) when is_binary(error) do
    %Tornium.API.Error{code: 6, error: error, message: "Wrong ID value."}
  end

  def construct(7, error) when is_binary(error) do
    %Tornium.API.Error{
      code: 7,
      error: error,
      message: "A requested selection is private (For example, personal data of another user / faction)."
    }
  end

  def construct(8, error) when is_binary(error) do
    %Tornium.API.Error{
      code: 8,
      error: error,
      message: "Current IP is banned for a small period of time because of abuse."
    }
  end

  def construct(9, error) when is_binary(error) do
    %Tornium.API.Error{code: 9, error: error, message: "API system is currently disabled."}
  end

  def construct(10, error) when is_binary(error) do
    %Tornium.API.Error{
      code: 10,
      error: error,
      message: "Current key can't be used because owner is in federal jail."
    }
  end

  def construct(11, error) when is_binary(error) do
    %Tornium.API.Error{code: 11, error: error, message: "You can only change your API key once every 60 seconds."}
  end

  def construct(12, error) when is_binary(error) do
    %Tornium.API.Error{code: 12, error: error, message: "Error reading key from database."}
  end

  def construct(13, error) when is_binary(error) do
    %Tornium.API.Error{code: 13, error: error, message: "The key owner hasn't been online for more than 7 days."}
  end

  def construct(14, error) when is_binary(error) do
    %Tornium.API.Error{
      code: 14,
      error: error,
      message: "Too many records have been pulled today by this user from our cloud services."
    }
  end

  def construct(15, error) when is_binary(error) do
    %Tornium.API.Error{
      code: 15,
      error: error,
      message: "An error code specifically for testing purposes that has no dedicated meaning."
    }
  end

  def construct(16, error) when is_binary(error) do
    %Tornium.API.Error{
      code: 16,
      error: error,
      message: "A selection is being called of which this key does not have permission to access."
    }
  end

  def construct(17, error) when is_binary(error) do
    %Tornium.API.Error{code: 17, error: error, message: "Backend error occurred, please try again."}
  end

  def construct(18, error) when is_binary(error) do
    %Tornium.API.Error{code: 18, error: error, message: "API key has been paused by the owner."}
  end

  def construct(19, error) when is_binary(error) do
    %Tornium.API.Error{code: 19, error: error, message: "The key owner hasn't migrated to crimes 2.0."}
  end

  def construct(20, error) when is_binary(error) do
    %Tornium.API.Error{code: 20, error: error, message: "This race has not finished yet."}
  end

  def construct(21, error) when is_binary(error) do
    %Tornium.API.Error{code: 21, error: error, message: "Invalid category value."}
  end

  def construct(22, error) when is_binary(error) do
    %Tornium.API.Error{code: 23, error: error, message: "Selection only available in API v1."}
  end

  def construct(23, error) when is_binary(error) do
    %Tornium.API.Error{code: 24, error: error, message: "Selection only available in API v2."}
  end

  def construct(24, error) when is_binary(error) do
    %Tornium.API.Error{code: 25, error: error, message: "Closed temporarily."}
  end
end
