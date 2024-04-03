.. _verification:

Verification
============
Similar to many other Torn-related Discord bots, Tornium supports verifying members with varying options. You can find the configuration for these options below.

.. note::
    Due to restrictions with Discord's permission system, Tornium will be unable to modify the nicknames and roles of server members with a role higher than the bot's highest role or the server owner. Changes to these members will have to be done manually by a server administrator. Server owners are considered to be the highest role in the server (and the role can't be modified), so the bot will never be able to verify them.

Verification Options
--------------------
Tornium supports verification of server members by verification status, faction, and faction position.

.. note::
    Many of these features have buttons to enable and disable them. This allows you to save your settings while the feature isn't being used. But you need to make sure that it's enabled when you wish for it to be in use.

Verification Log Channel
````````````````````````
Verification details such as member roles changed will be logged to this specified log channel if enabled.

.. warning::
   This feature is somewhat spammy if there are many members of the server that aren't verified or need to be changed.

Verified Name
`````````````
For applicable members (see above), while being verified, Tornium bot will change their nickname to reflect a passed `Jinja2 <https://jinja.palletsprojects.com/en/3.1.x/>`_ template. The default template is ``{{ name }} [{{ tid }}]`` such that the nickname of `tiksan <https://www.torn.com/profiles.php?XID=2383326>`_ will be set to ``tiksan [2383326]``.

.. list-table:: Available Jinja Variables
    :header-rows: 1

    * - Syntax
      - Definition
    * - ``{{ name }}``
      - Torn username
    * - ``{{ tid }}``
      - Torn ID
    * - ``{{ tag }}``
      - Torn faction tag

Exclusion Roles
```````````````
Tornium will skip verifying certain members if they have a certain role. For example, this can be used for faction members that are guesting.

Daily Automatic Reverification
``````````````````````````````
When enabled, this will automatically re-verify all members of the server once a day at a pre-determined time specified on the server's verification dashboard (determined from the server's ID) logging to the verification log channel is enabled.

Verification by Status
``````````````````````
Discord users can link their Discord account to their Torn account through the `official Torn Discord server <https://torn.com/discord>`_. This allows servers to verify the identities of their members. This feature allows server administrators to give verified server members specific role(s) and/or change their server nickname.

Verification by Faction
```````````````````````
This feature allows servers to verify their members and give them roles based on their faction ID. The faction ID doesn't need to match the faction IDs that are set up to be used in the server.

Verification by Faction Position
````````````````````````````````
This feature allows servers to give members roles based on their position in their faction. These roles will be removed if a member changes factions and/or faction roles. For this feature to work, the faction must set the server as their server (for information, check out ...).

.. note::
   The person setting up this feature must be an AA member of the faction (to avoid leaking potentially sensitive data), and there must be an available AA key from that faction.

Miscellaneous Options
`````````````````````
Tornium can post messages regarding verification status to a specific channel. This can be set up in the verification dashboard under "Basic Verification Configuration".

Server administrators can specify and give exclusion role(s) that causes Tornium to skip members who are attempting to be verified. This configuration can be located under "Verified Role and Names" in the verification dashboard.

Verification Slash Commands
---------------------------
There are two verification slash commands currently: one to verify a single user and another to verify all server members. Verification can not be configured through slash commands.

Verify
``````
.. code-block::

    /verify [member] [force]

Verifies a single member in the Discord server. Updates the member's nickname and/or roles depending on server configuration as detailed `above <Verification Options>`_.

For a member to be successfully verified by Tornium, they must be verified through the `official Torn Discord server <https://torn.com/discord>`_.

.. list-table::
    :header-rows: 1

    * - Argument
      - Definition
      - Required
      - Default
    * - ``member``
      - Mentioned Discord member
      - False
      - Command invoker
    * - ``force``
      - Force new data via Torn API calls
      - False
      - True

Verify All Members
``````````````````
.. code-block::

    /verifyall [force]

Verifies all members in the Discord server in a background task. Attempts to update the members' nicknames and/or roles depending on the server configuration as detailed `above <Verification Options>`_.

For a member to be successfully verified by Tornium, they must be verified through the `official Torn Discord server <https://torn.com/discord>`_.

.. list-table::
    :header-rows: 1

    * - Argument
      - Definition
      - Required
      - Default
    * - ``force``
      - Force new data via Torn API calls
      - False
      - True

.. note::
    Due to resource limitations and Discord ratelimiting, a decreased number of log messages will be sent to the specified log channel.
