defmodule Tornium.Notification.Delivery do
  # TODO: Add docs
  @callback render(state :: map(), notification :: Tornium.Schema.Notification.t()) ::
              {:ok, rendered_template :: String.t()} | {:error, error :: term()}

  @callback validate(rendered :: String.t()) :: {:ok, validated :: map()} | {:error, error :: term()}

  @callback deliver(rendered :: map(), notification :: Tornium.Schema.Notification.t()) ::
              {:ok, output :: term()} | {:error, error :: term()}
end
