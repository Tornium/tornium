.. _stakeouts:

Stakeouts
=========
Tornium can send notifications in direct messages or in a channel when certain user or faction criteria are met. Unlike most of the bot's other features, stakeouts are entirely configured via slash commands.

Stakeout Slash Commands
-----------------------
All commands can be run in DMs or in a server depending on if you want the notifications to be sent in a DM or in the server.

.. warning::
   It is recommended to create notifications in a server. Discord will block messages detected to be spam to users' DMs, and potentially can block the bot from sending DMs to anyone.

.. note::
    For stakeout slash commands (other than the initialization of the stakeout), there will be an optional ``type`` parameter if there's a stakeout on two objects with the same ID.

Initialize Stakeout
````````````````````
.. code-block::

    /notify stakeout initialize (type) (tid) [channel]

Initializes the stakeout in the database. Initially, there are no categories set for the stakeout and the stakeout is not enabled.

If a channel is mentioned in a server, the notifications will be sent in that channel. Otherwise, the notifications will be sent in a DM to the user.

.. list-table::
    :header-rows: 1

    * - Argument
      - Definition
      - Required
      - Default
    * - type
      - Stakeout type
      - True
      -
    * - tid
      - Torn ID of the user or faction
      - True
      -
    * - channel
      - Channel for the notification to be sent in
      - False
      - DM with the invoker

Toggle Stakeout Category
````````````````````````
.. code-block::

    /notify stakeout category (tid) (category) [type]

Toggle a stakeout category for the mentioned stakeout. By default all categories are disabled.

.. list-table::
    :header-rows: 1

    * - Argument
      - Definition
      - Required
      - Default
    * - tid
      - Torn ID of the user or faction
      - True
      -
    * - category
      - Stakeout category to toggle
      - True
      -
    * - type
      - Stakeout type
      - False
      -

Enable Stakeout
```````````````
.. code-block::

    /notify stakeout enable (tid) [type]

Enable the mentioned stakeout if not already enabled.

.. list-table::
    :header-rows: 1

    * - Argument
      - Definition
      - Required
      - Default
    * - tid
      - Torn ID of the user or faction
      - True
      -
    * - type
      - Stakeout type
      - False
      -

Disable Stakeout
````````````````
.. code-block::

    /notify stakeout disable (tid) [type]

Disable the mentioned stakeout if not already disabled.

.. list-table::
    :header-rows: 1

    * - Argument
      - Definition
      - Required
      - Default
    * - tid
      - Torn ID of the user or faction
      - True
      -
    * - type
      - Stakeout type
      - False
      -

List Stakeouts
``````````````
.. code-block::

    /notify stakeout list

List all stakeouts that are in the server or your DMs.

Delete Stakeout
```````````````
.. code-block::

    /notify stakeout delete (tid) [type]

Delete the mentioned stakeout.

.. list-table::
    :header-rows: 1

    * - Argument
      - Definition
      - Required
      - Default
    * - tid
      - Torn ID of the user or faction
      - True
      -
    * - type
      - Stakeout type
      - False
      -

Stakeout Info
`````````````
.. code-block::

    /notify stakeout info (tid) [type]

Return information about the mentioned stakeout.

.. list-table::
    :header-rows: 1

    * - Argument
      - Definition
      - Required
      - Default
    * - tid
      - Torn ID of the user or faction
      - True
      -
    * - type
      - Stakeout type
      - False
      -
