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
The whitelist of factions that can send assist requests to that server.

Assist Roles
````````````
There are certain roles that can be configured for different types of positions in the attack.

Smoker Role
~~~~~~~~~~~
Users to be pinged when there's a request for a smoke to be used.

Tear Role
~~~~~~~~~
Users to be pinged when there's a request for a tear to be used.

500M+ Heavy Role
~~~~~~~~~~~~~~~~
Role for members that are 500m+ total. This role is also used as a generic role for heavies when necessary.

1B+ Heavy Role
~~~~~~~~~~~~~~
Role for members that are 1b+ total.

2B+ Heavy Role
~~~~~~~~~~~~~~
Role for members that are 2b+ total.

5B+ Heavy Role
~~~~~~~~~~~~~~
Role for members that are 5b+ total.

Assist Servers
``````````````
The servers that can receive an assists request from your faction.

Assist Slash Command
--------------------
Assist
``````
Sends an assist request on the specified target to all applicable servers.

.. warning::
   This command is disabled pending a rewrite.

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

