# Install Bot to Discord Server
In this tutorial, we will be installing the Tornium Discord bot to a Discord server. Installing the bot will require at least the manage server permission on the Discord server, but configuring the bot for the Discord server will require additional permissions: at least administrator permissions on the Discord server.

## Adding the Bot
First, we will be adding the bot to the Discord server. Installation can be done through this [Discord invite link](https://discord.com/api/oauth2/authorize?client_id=979105784627593266&permissions=469969968&scope=bot%20applications.commands) with the minimal permissions required. This Discord invite link will open a Discord page for you to select the server to invite the bot to. After pressing continue, Discord will list the permissions you are granting the bot in the selected server. You will then press "Authorize" on this page to invite the bot to the selected Discord server.

At this point, the Discord bot will be added to the selected Discord server. We can verify that the bot has been added to the server by finding Tornium in the member list of the server. Now that the bot has been added to the server, we can now start configuring the bot for this server.

## Configuring the Bot
Now that the bot has been added to the Discord server, you will need to wait for Tornium to store the Discord server in its database. This can take up to an hour to occur. If you have administrator permissions on the Discord server, you will be able to see that the bot has been added to the database when the Discord server is listed on the [Server Selector](https://tornium.com/bot/dashboard) on Tornium's website.

Once the Discord server is listed on the "Server Selector", we can now start configuring features for the Discord server. You will need to select the specific Discord server with the "Edit Server" button. After pressing the "Edit Server" button, you will be redirected to the main bot configuration page for the selected Discord server. On this page, you will be able to set up various features for the bot on this Discord server.

For information on configuring specific features, follow these tutorials:
- [Setup Verification](discord-server-verification.md)
- [Setup Organized Crimes](discord-server-oc.md)
- [Setup Notifications](discord-server-notification.md)
