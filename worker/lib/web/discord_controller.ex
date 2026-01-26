defmodule Tornium.Web.DiscordController do
  use Tornium.Web, :controller

  def connect(%Plug.Conn{body_params: body_params} = conn, _params) do
    %URI{path: path, query: query} =
      body_params
      |> Map.fetch!("endpoint")
      |> URI.parse()

    response =
      if is_nil(query) do
        Nostrum.Api.request(
          body_params
          |> Map.fetch!("method")
          |> method(),
          path,
          Map.get(body_params, "body", "")
        )
      else
        Nostrum.Api.request(
          body_params
          |> Map.fetch!("method")
          |> method(),
          path,
          Map.get(body_params, "body", ""),
          query
          |> URI.decode_query()
          |> Enum.into([], fn {k, v} -> {String.to_atom(k), v} end)
        )
      end

    case response do
      :ok ->
        conn
        |> send_resp(204, "")

      {:ok, response_blob} when is_binary(response_blob) ->
        conn
        |> put_status(200)
        |> json(response_blob |> JSON.decode!())

      {:error, %Nostrum.Error.ApiError{status_code: status_code, response: response_json}} ->
        conn
        |> put_status(status_code)
        |> json(response_json)
    end
  end

  defp method(value) when is_binary(value) do
    case String.downcase(value) do
      "delete" -> :delete
      "get" -> :get
      "post" -> :post
      "patch" -> :patch
      "put" -> :put
    end
  end
end
