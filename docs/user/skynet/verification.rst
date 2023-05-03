.. _verification:

SkyNet Verification
===================
Similar to many other Torn-related Discord bots, SkyNet supports verifying members with varying options. You can find the configuration for these options below.

.. note::
    Due to restrictions with Discord's permission system, SkyNet will be unable to modify the nicknames and roles of server members with a role higher than the bot's highest role or the server owner. Changes to these members will have to be done manually by a server administrator.

.. warning::
    Due to resource limitations, Tornium does not support automatic daily verification at this time. The ``/verifyall`` slash command will have to be run manually instead of an automatic schedule job.

Verification Options
--------------------
SkyNet supports verification of server members by verification status, faction, and faction position.

.. note::
    Many of these features have buttons to enable and disable them. This allows you to save your settings while the feature isn't being used. But you need to make sure that it's enabled when you wish for it to be in use.

Verified Name
`````````````
For applicable members (see above), while being verified SkyNet will change their nickname to reflect a passed `Jinja2 <https://jinja.palletsprojects.com/en/3.1.x/>`_ template. The default template is ``{{ name }} [{{ tid }}]`` such that the nickname of `tiksan <https://www.torn.com/profiles.php?XID=2383326>`_ will be set to ``tiksan [2383326]``.

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

.. warning::
    The ``{{ tag }}`` variable has not been implemented yet.

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
    There must be an AA member from this faction signed into Tornium for this feature to work.

Miscellaneous Options
`````````````````````
SkyNet can post messages regarding verification status to a specific channel. This can be set up in the verification dashboard under "Basic Verification Configuration".

Server administrators can specify and give exclusion role(s) that causes SkyNet to skip members who are attempting to be verified. This configuration can be located under "Verified Role and Names" in the verification dashboard.


Verification Slash Commands
---------------------------
There are two verification slash commands currently: one to verify a single user and another to verify all server members. Verification can not be configured through slash commands.

Verify
``````
.. code-block::

    /verify [member] [force]

Verifies a single member in the Discord server. Updates the member's nickname and/or roles depending on server configuration as detailed `above <Verification Options>`_.

For a member to be successfully verified by SkyNet, they must be verified through the `official Torn Discord server <https://torn.com/discord>`_.

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

For a member to be successfully verified by SkyNet, they must be verified through the `official Torn Discord server <https://torn.com/discord>`_.

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
