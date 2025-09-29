# Setup Overdose Reporting
In this tutorial, we will be setting up overdose reporting for a faction in a linked Discord server. This will send notifications when a member of the faction overdoses. Before starting, you will need to have completed the following steps:
1. [Bot installation](discord-server-installation.md): Install the bot in your Discord server
2. [Faction-server linking](discord-server-link.md): Link your faction and Discord server together
3. Create a channel to use for overdose notifications.

## Overdose Reporting Configuration
Now that we have a faction and server linked and channel set up for notifications, we will open the Discord server's dashboard. Select your Discord server on Tornium's [server selector](https://tornium.com/bot/dashboard) to open your server's dashboard. The section for overdose notifications can be found under the `Faction Overdoses` header. This faction overdose section contains all the configuration options for overdose notifications for factions in your Discord server.

Find your faction's name in this section. Next to the faction's name, there will be two select boxes for the overdose channel and the overdose policy respectively. In the first select box, choose the Discord channel you'd previously created. And in the second select box, choose one of the two policy options:
1. Daily: A daily report will be sent around midnight TCT listing all overdoses over the last 24 hours.
2. Immediate: A notification will be sent as the overdoses are noticed.

You can ensure that the settings have saved by refreshing the page and checking the roles are still listed. At this point, we have now set up faction banking for your Discord server. For more information, see the [overdose notification reference](../reference/bot-overdose.md) page.
