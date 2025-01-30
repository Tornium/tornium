.. _creating_triggers:

Creating New Triggers
=====================
Anyone can create new triggers on `Tornium <https://tornium.com/notification/trigger/create>`_, and this page is meant to document the internals of triggers for developers of custom triggers.

.. warning::
   As stated in Tornium's `Terms of Service <https://tornium.com/terms>`_, you are not allowed to use this feature to disrupt Tornium. Even if the sandboxing of this feature is not perfect, intentionally malicious use of this feature is not permitted and may result in a banning of the user, the user's faction, and/or the user's Discord server from Tornium.

.. note::
   Currently, the creation of new triggers is disabled while notifications are still being tested publicly. Only official triggers can be used.

Alert Conditions
~~~~~~~~~~~~~~~~
The *name* and *description* of the trigger are mostly self-explanatory. The *trigger resource* is the "resource" in the API to be used to retrieve data against. The cron determines how when the notifications for this trigger will be executed (for more information, see `this guide <https://crontab.guru/>`_ and the `man pages <https://www.man7.org/linux/man-pages/man5/crontab.5.html>`_).

.. note::
   The only supported resources currently are `user` and `faction` on API v1, but more will be added as time passes.

Trigger Conditions
~~~~~~~~~~~~~~~~~~
This section is for the code to insert the code for the trigger to run. The code will be run using the `Lua <https://lua.org/>`_ programming language and `Luerl <https://luerl.org/>`_ (a Lua runtime). It is suggested to write this trigger in a separate text editor as Tornium does not provide any syntax highlighting, squiggly lines, etc. other than basic validation (through `luac <https://www.lua.org/manual/5.4/luac.html>`_).

The Lua code in this is not required to be inside of a function, but values do need to be returned. Specifically, the code must return in the form `boolean, table, table`. The first value will represent whether the trigger has been tripped (i.e. whether a message will be sent for this). The second value will represent the values to be passed to the Liquid template for the message. The third value will represent the values to be added to the state to be provided for future executions of the trigger.

The parameters represent values that will be injected into Lua code before runtime (acting essentially as a pre-processor). It is recommended to use capitalized names for these variables (e.g. ``USER_ID``) for readability.

Trigger Message
~~~~~~~~~~~~~~~
This section is to specify how the Discord message will be updated (if the Lua code indicated that a message should be sent). The toggle for message type allows for the existing message to be updated or for a new message to be sent every time.

The message template uses the `Liquid templating language <https://shopify.github.io/liquid/>`_. You can use the state provided from the code in this template. This template must be in the form of a `Discord message object <https://discord.com/developers/docs/resources/message#create-message>`_ and be valid JSON.

.. note::
   The Liquid templates are validated on the client with `LiquidJS <https://liquidjs.com/>`_ but rendered with `Solid <https://hexdocs.pm/solid/readme.html>`_ (the Elixir implementation of Liquid), so there may be differences in the implementations.

API Calls
~~~~~~~~~
TODO
