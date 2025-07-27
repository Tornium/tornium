# Setup Notifications
In this tutorial, we will be setting up notifications in a Discord server. Notifications are a powerful, complex tool allowing custom notifications of in-game actions and events. You can build your own notifications triggers (soon; this is not yet released) or you can use pre-built, official notification triggers. This tutorial will only go over how to setup pre-built, official notification triggers; for more information on notifications and notification triggers, visit the [notification reference](../reference/notification.md) and the [notification trigger reference](../reference/notification-trigger.md).

***WARNING:*** As stated in Tornium's [ToS](https://tornium.com/terms), you are not allowed to use this feature to disrupt Tornium. Intentionally malicious use of this feature is not permitted.

## Terminology
**Notification Trigger**: generic user-provided code providing the logic and message for notifications when installed

**Official Notification Trigger**: notification triggers provided by Tornium for use by everyone

**Restricted Notification Trigger**: notification triggers utilizing non-public information (see the [notification trigger reference](../reference/notification-trigger.md))

**Notification**: installed notification triggers configured for certain parameters

**Parameters**: values in notification triggers defined by end-users determining the behavior of the notification

## Example
For example, a notification to send a message when a certain stock is below a certain price would look like the following:

**Notification Trigger**: the code that checks the stock price and the message it'll send when the stock price is below the target price

**Parameters**: the stock to check (e.g. FHG) and the target stock price (e.g. $770)

Then whenever the stock is below the target stock price, the bot will determine that the notification trigger has been activated and will send a message in a specific channel with the message the notification trigger provides.

## Setting up a Notification
Now that you understand what notifications and notification triggers are, we can set up an official notification trigger. First you will need to view Tornium's list of the official notification triggers under [`Notification > Notification Triggers`](https://tornium.com/notification/trigger). The section under `Official Notification Triggers` lists the official triggers for use by anyone. For information on each of the official notification triggers, visit the [notification trigger reference](../reference/notification-trigger.md).

Once you find the notification trigger you want to install, you can press the plug button next to the trigger to add the trigger to a Discord server you are an admin in (Tornium's bot must be in this server). This will open a page providing a full description of the notification trigger. You will need to select which Discord server you will install the notification trigger to. Upon pressing "Add Trigger", you will be sent to a page to configure the notification trigger. Here, you will select the notification channel, the resource ID, and a one-shot flag and then you will fill in the notification trigger's parameters. This will be described in depth below:

The notification channel is the Discord channel where messages for the notification trigger will be sent when the trigger is activated. The resource ID is the ID of the user, faction, etc. the notification trigger will be acting upon. The one-shot flag determines how many times the notification trigger can be activated before the notification is deleted, but you should follow the instructions provided in the notification trigger's description when setting this value. The notification triggers are parameters provided by the developer of the notification trigger to provide additional configuration, and once again you will need to follow the instructions provided in the description of the notification trigger.

Once the notification trigger has been configured, you can press the "Setup Trigger" button for the notification trigger to be installed into the Discord server. At this point, the notification will now be running until the notification is deleted or disabled. For more information on notifications and notification triggers, visit the [notification reference](../reference/notification.md) and the [notification trigger reference](../reference/notification-trigger.md).

## Bot Configuration
TODO
