.. _notifications_index:

Tornium Notifications
=====================
Tornium supports more complicated notifications of in-game actions and events. You can build your own notification triggers or you can use pre-built notification triggers.

.. warning::
   As stated in Tornium's `Terms of Service <https://tornium.com/terms>`_, you are not allowed to use this feature to disrupt Tornium. Even if the sandboxing of this feature is not perfect, intentionally malicious use of this feature is not permitted and may result in a banning of the user, the user's faction, and/or the user's Discord server from Tornium.

Terminology
-----------
| Triggers: generic user-provided code to determine when to send a message and what message to send for the notification
| Notifications: installed triggers that are set for certain parameters
| Parameters: values in triggers that end-users can define

Example
~~~~~~~
| For a notification to send a message when a certain stock is less than a certain price, it would look like the following...

| The parameters in this notification would the stock you want to check (e.g. FHG) and the target stock price (e.g. $770).
| The trigger would be some Lua code that checks when the price of the stock in the parameters is less than the price defined in the parameter. The trigger would also define some message about how that stock has reached some target that would be sent in Discord.
| The notification would define what the stock and target stock price would be. Then the notification would say which server and channel the messages should be sent to.

Setting Up a Trigger
--------------------
Create new triggers on `Tornium <https://tornium.com/notification/trigger/create>`_. For more information regarding setting up notifications, take a look at the :ref:`feature's full documentation<creating_triggers>`.

Alert Conditions
~~~~~~~~~~~~~~~~
The *name* and *description* of the trigger are mostly self-explanatory. The *trigger resource* is the "resource" in the API to be used to retrieve data against. The cron determines how when the notifications for this trigger will be executed (for more information, see `this guide <https://crontab.guru/>`_ and the `man pages <https://www.man7.org/linux/man-pages/man5/crontab.5.html>`_).

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

Setting Up a Notification
-------------------------
.. note::
    Currently, notifications can only be created for a channel in a Discord server, but are designed such that they can be sent to the browser in the future.

This part of the feature has not yet been implemented.
