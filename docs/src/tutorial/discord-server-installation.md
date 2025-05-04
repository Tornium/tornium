# Install Bot to Discord Server
In this tutorial, we will install the Tornium Discord bot to a Discord server. Installing the bot will require at least the manage server permission on the Discord server, but configuring the bot for the Discord server will require additional permissions: at least administrator permissions on the Discord server.

## Adding the Bot
First, we must add the bot to the Discord server. We suggest using this [Discord invite link](https://discord.com/api/oauth2/authorize?client_id=979105784627593266&permissions=469969968&scope=bot%20applications.commands) with the minimal permissions required instead of giving the bot the Administrator permissions. This Discord invite link will open a Discord page for us to select the server to invite the bot to. After pressing continue, Discord will list the permissions we are granting the bot. We will press "Authorize" on this page to invite the bot to the selected Discord server.

At this point, the Discord bot will be added to the selected Discord server. We can verify that the bot has been added to the server by finding Tornium in the member list of the server. Now that the bot has been added to the server, we can now start configuring the bot for this server.

## Configuring the Bot
First, we must wait for Tornium to store the Discord server in its database. This can take up to an hour to occur. If we have administrator permissions on the Discord server, we can see that the bot has been added to the database when the Discord server is listed on the [Server Selector](https://tornium.com/bot/dashboard) on Tornium's website.

Once the Discord server is listed on the "Server Selector", we can select the specific Discord server with the "Edit Server" button. After pressing the "Edit Server" button, we will be redirected to the main bot configuration page for the selected Discord server. On this page, we will be able to set up various features for the bot on this Discord server.
