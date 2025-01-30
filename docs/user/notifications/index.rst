.. _notifications_index:

Tornium Notifications
=====================
Tornium supports more complicated notifications of in-game actions and events. You can build your own notification triggers or you can use pre-built notification triggers (see the :ref:`docs<creating_triggers>` page for more information on creating your own triggers).

.. warning::
   As stated in Tornium's `Terms of Service <https://tornium.com/terms>`_, you are not allowed to use this feature to disrupt Tornium. Even if the sandboxing of this feature is not perfect, intentionally malicious use of this feature is not permitted and may result in a banning of the user, the user's faction, and/or the user's Discord server from Tornium.

Terminology
-----------
| Triggers: generic user-provided code to determine when to send a message and what message to send for the notification
| Official Trigger: a trigger provided by the developers of Tornium for all to use
| Notifications: installed triggers that are set for certain parameters
| Parameters: values in triggers that end-users can define

Example
~~~~~~~
| For a notification to send a message when a certain stock is less than a certain price, it would look like the following...

| The parameters in this notification would the stock you want to check (e.g. FHG) and the target stock price (e.g. $770).
| The trigger would be some Lua code that checks when the price of the stock in the parameters is less than the price defined in the parameter. The trigger would also define some message about how that stock has reached some target that would be sent in Discord.
| The notification would define what the stock and target stock price would be. Then the notification would say which server and channel the messages should be sent to.

Creating a Notification for a Server
------------------------------------
.. note::
    Currently, notifications can only be created for a channel in a Discord server, but are designed such that they can be sent to the browser in the future.

You can create a notification from a notification trigger. Official triggers can be used by anyone while only the creator of a trigger can use their trigger. A list of official and the user's triggers can be found under `Notification -> Notification Triggers <https://tornium.com/notification/trigger>`_. By pressing the plus button next to the trigger, you can add the trigger to a Discord server Tornium is in and where you're an admin. Follow the prompts to select which server to add the trigger to. Then you can select the channel messages will be sent to, the ID of the faction/user/etc., and any other necessary data. Additionally, you'll need to select if the notification should be one-shot or repeating; one-shot notifications will only trigger once and repeating notifications will continue to send messages until the notification is deleted.

.. note::
    Currently, only official triggers can be used to create notifications while this feature is being tested.

Once the notification is created, you can access your server's list of notifications on your server's dashboard. There server admins can modify the configuration of their notifications and delete notifications.
