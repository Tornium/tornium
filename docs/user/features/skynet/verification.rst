.. _verification

SkyNet Verification
===================
Similar to many other Torn-related Discord bots, SkyNet supports verifying members with varying options. You can find the configuration for these options below.

..  contents::
    :local:

.. note::
    Due to restrictions with Discord's permission system, SkyNet will be unable to modify the nicknames and roles of server members with a role higher than the bot's highest role or the server owner. Changes to these members will have to be done manually by a server administrator.

Verification Options
--------------------
SkyNet supports verification of server members by verification status, faction, and faction position.

.. note::
    Many of these features have buttons to enable and disable them. This allows you to save your settings while the feature isn't being used. But you need to make sure that it's enabled when you wish for it to be in use.

Verified Name
`````````````
For applicable members (see above), while being verified SkyNet will change their nickname to reflect a passed Jinja2 template. The default template is ``{{ name }} [{{ tid }}]`` such that the nickname of `tiksan <https://www.torn.com/profiles.php?XID=2383326>`_ will be set to ``tiksan [2383326]``.

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
Under construction.

Verification by Faction Position
````````````````````````````````
Under construction.

Miscellaneous Options
`````````````````````
SkyNet can post messages regarding verification status to a specific channel. This can be set up in the verification dashboard under "Basic Verification Configuration".

Server administrators can specify and give exclusion role(s) that causes SkyNet to skip members who are attempting to be verified. This configuration can be located under "Verified Role and Names" in the verification dashboard.
