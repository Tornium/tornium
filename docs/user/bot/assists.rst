.. _assists:

Assists are currently in the process of being rebuilt.

Assist Requests
===============
Members can send requests to other members of the server and to other applicable servers that request members to join the attack and help take down a target.

Assist Options
--------------
Assists can be set up through the bot dashboard under ``Assist Requests``. When setting various settings, make sure to press the submit button.

Assist Channel
``````````````
The assist channel is the channel to which all applicable assist requests will be forwarded.

Assist Factions
```````````````
This is the list of factions that are selected to apply the assist forwarding option upon.

.. note::
    During the v0.5.x release cycle, when forwarding is modified to a whitelist instead of a selection, this list of factions will be the list of whitelisted factions.

Assist Forwarding Options
`````````````````````````
This list of options represents how incoming assist requests are filtered.

If ``whitelist`` is selected, only assist requests from factions listed in the ``Assist Factions`` will be sent on the server.
If ``blacklist`` is selected, only assist requests not from the factions listed in the ``Assist Factions`` will be on the server.
If ``global`` is selected, any and all assist requests will be sent on the server.

.. warning::
    Assist forwarding options are deprecated and will be removed in favor of a permanent whitelist during the v0.5.x release cycle.

Assist Slash Command
--------------------
Assist
``````
Sends an assist request on the specified target to all applicable servers.

.. list-table::
    :header-rows: 1

    * - Argument
      - Definition
      - Required
      - Default
    * - ``tornid``
      - The Torn ID of the target
      - False
      -
    * - ``url``
      - The attack loader URL of the target
      - False
      -

