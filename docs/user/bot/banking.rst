.. _banking:

Faction Banking
===============
Members can send vault requests via Tornium to validate the requests and notify faction bankers.

Banking Options
---------------
As a slash command, faction banking can be run from any channel in a faction's Discord server or from the Tornium website. Vault requests will be forwarded to a specific channel and with an optional ping to faction banker role(s).

.. note::
    Currently, withdrawal requests can only be run in servers or via the website.

Banking Channel
```````````````
Banking requests will be forwarded to this channel when a vault request is sent. If the channel is marked as "Disabled", vault requests will not be allowed.

Banker Roles
````````````
Banking requests will ping the selected roles upon vault request messages, but banker roles are not required.

Banking Slash Commands
----------------------
Only the ``/balance`` command can be run in DMs; everything else can only be run in the faction's server.

Balance
```````
.. code-block::

    /balance [member]

Returns the member's vault balance of money and points in their current faction.

If the command is run in a Discord server and the invoker has API access in the faction, a member can be mentioned to obtain their vault balance.

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

Withdraw
````````
.. code-block::

    /withdraw (amount) [option]

Sends a vault request to the banking channel and mentions the banker roles if banking is enabled by the faction.

A vault request will be marked as cancelled if it is not fulfilled within one hour of the request.

.. list-table::
    :header-rows: 1

    * - Argument
      - Definition
      - Required
      - Default
    * - ``amount``
      - Amount to be requested from the faction vault
      - True
      -
    * - ``option``
      - Whether points or cash should be withdrawn
      - False
      - Cash withdrawals

The ``amount`` parameter allows for the suffixes used by Torn to shorten money amounts. Additionally ``all`` can be used to request all of the member's vault balance.

.. list-table::
    :header-rows: 1

    * - Suffix
      - Amount
    * - 1K
      - 1,000
    * - 1M
      - 1,000,000
    * - 1B
      - 1,000,000,000

Fulfill
```````
.. code-block::

    /fulfill (id)

Marks a vault request as fulfilled.

.. list-table::
    :header-rows: 1

    * - Argument
      - Definition
      - Required
      - Default
    * - ``id``
      - Withdrawal ID
      - True
      -

Cancel
``````
.. code-block::

    /cancel [id]

Marks a vault request as cancelled. Cancels the last request if no withdrawal ID is specified.

.. list-table::
    :header-rows: 1

    * - Argument
      - Definition
      - Required
      - Default
    * - ``id``
      - Withdrawal ID
      - True
      -
