.. _retals:

Retaliations
============
This will send notifications to a specified channel when an attack can be retaliated against. The automatic task for this feature runs every 15 seconds currently.

.. note::
   Retaliations are somewhat API intensive, so please disable this feature if you aren't using it.

If retals are configured in the server's bot dashboard, retal notifications will be sent unless the attack is a non-war, overseas attack.

Retaliation Options
-------------------
Tornium will automatically add each faction currently verified to be in the faction to the list of possible factions for retaliations. Factions not in that list can not be used for retaliations.

Retaliation Channel
```````````````````
Retaliation notifications are sent to this channel if enabled. Select ``Disabled`` to disable retaliation notifications from that faction.

Retaliation Roles
`````````````````
Retaliations notifications ping these roles when sent if any are set.
