.. _crimes

Faction Organized Crimes
========================
Tornium can parse and store organized crimes which can be used for OC payouts, OC team modifications, and more.

.. note::
    This feature is currently in development and is not yet feature complete. As such, this documention may indicate the previous or future state of the code.

Pending Crimes
--------------
This is a list of organized crimes that haven't yet been initiated as of the last API call to update this information. This includes when the OC should have been initiated/was ready.

In-Progress Crimes
------------------
This is a list of organized crimes that are currently in progress and when the OC should be initiated.

Organized Crime Filter/Viewer
-----------------------------
Users can look through organized crimes of their faction, the status of the OC, and more. This feature will be used to determine payouts in the future.

.. note::
   Tornium does not store the reason for a delay, only that a user delayed an OC. As such, to the database, there isn't a difference between a user being in the hospital for a minute and a user flying to China. If you wish to have such data, the Discord bot's notifications include this data. See :ref:`the bot OC notifications<ocnotifs>`
