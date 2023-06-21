.. _stocks:

Stock Notifications
===================
Tornium can send notifications for stocks movements and other stock information.

Stock Movement Notifications
----------------------------
Stock movement notifications will send notifications in a DM or a specified channel when a stock passes through a specified threshold. These notifications are currently only set up entirely through slash commands.

For example, if FHG is at $759.81 with a notification to be sent with a greater than equality and a price of $760, the notification will be sent the first time that FHG's price goes above $760.

Create Stock Notification
`````````````````````````
.. code-block::

    /stocks notify create (stock) (price) (equality) [private] [channel]

Creates a notification for when the specified stock goes above or below the specified threshold.

.. list-table::
    :header-rows: 1

    * - Argument
      - Definition
      - Required
      - Default
    * - ``stock``
      - Stock's acronym
      - True
      -
    * - ``price``
      - Threshold price to notify at
      - True
      -
    * - ``equality``
      - Equality to compare with the threshold price (i.e. ``>``, ``<``, ``=``)
      - True
      -
    * - ``private``
      - Whether the notification should be sent in a DM or in a specified channel
      - False
      - True
    * - ``channel``
      - Discord channel that notifications will be sent to
      - False
      -

.. note::
    If the notification is to be sent to a specified channel, private also needs to be specified. This section is still under construction.

List Stock Notifications
````````````````````````
.. code-block::

    /stocks notify list [page]

List the user's stock notifications.

.. list-table::
    :header-rows: 1

    * - Argument
      - Definition
      - Required
      - Default
    * - ``page``
      - Which page of notifications are shown
      - False
      - 1st page

Delete Stock Notification
`````````````````````````
.. code-block::

    /stocks notify delete [notification]

Delete the specified notification by database ID (which can be found with the ``/stocks notify list`` command). All applicable notifications can be deleted by passing ``all`` instead of a database ID.

Stock Notification Feed
-----------------------
SkyNet will send all enabled feed options to a specified channel

.. warning::
    Stocks feed notifications are still under development and are currently disabled in all servers.
