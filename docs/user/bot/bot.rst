.. _bot:

Tornium Bot
===========
Tornium Bot (previously known as SkyNet) is Tornium's latest Discord bot built from scratch using the Discord API.

Inviting the Bot
----------------
Only members that have the server administrator permission will be allowed to set up the server. Certain features will require a faction's AA member to proceed.

You can invite Tornium Bot onto your server with either specific, required permissions or administrator permissions. The former is preferred for privacy/security reasons, but the latter will be easier to set up for most server administrators. However, unlike previous Discord bots, Tornium Bot relies entirely upon slash commands to call a command so the bot will be unable to read any messages posted in your servers.

 * Required permissions invite link: `<https://discord.com/api/oauth2/authorize?client_id=979105784627593266&permissions=275884682288&scope=applications.commands+bot>`_
 * Administrator permissions invite link: `<https://discord.com/api/oauth2/authorize?client_id=979105784627593266&permissions=8&scope=bot%20applications.commands>`_

.. note::
    Tornium bot utilizes an automated task to update the database's list of servers the bot is in (as well as the server's list of admin users). This automated task runs every hour, so it will take up to an hour for this to update from when the bot is invited into your server. Go out and touch some grass.

Faction Linking
---------------
Certain faction-oriented features will require the faction and server to link to each other to prevent someone from maliciously hijacking a faction's data or a server's channels/roles. It is recommended to do this through a slash command for ease of use but this can also be performed through the website. Regardless of how the faction is linked, an AA member of the faction would need to be signed into Tornium for the respective features to work as intended.

Slash Command
`````````````
The `/link` slash command can be run in Discord servers to set the faction's server to that server in which the command was invoked. However, the command invoker must be an AA member of the faction (although they don't need to be signed into Tornium). If the user is also an admin of the server, the bot will also add their faction to the server's list of factions.

Website
```````
An AA member of the faction will need to set their faction's server ID on the `faction bot page <https://tornium.com/faction/bot>`_ by enabling developer mode, right clicking on the server and copying the server ID. More information of finding the server ID can be found on `Discord's Knowledge Base <#>`_.

.. note::
   Due to browsers' implementation details, some browsers may not properly show an updated value in this field even if the data is updated. You can navigate away and return to the page to verify that the server ID is set as intended.

An admin of the server will need to navigate to the server's dashboard found through the `server selector <https://tornium.com/bot/dashboard>`_ and add the faction to the server's list of factions through the faction ID. The faction ID can be found in the URL of the faction when searching for the faction by name on Torn. After reloading the page, if the faction and server are properly linked, there will be a checkmark next to the faction's name and ID (otherwise, there will be a cross icon).

Bot Modules
-----------
Almost all of the bot's configuration will be done through the bot dashboard found on the `Tornium website <https://tornium.com/bot/dashboard>`_ but many user-oriented features can be found on the bot.

 * :ref:`Verification<verification>`
 * :ref:`Faction Banking<banking>`
 * :ref:`Retaliations<retals>`
 * :ref:`Organized Crime Notifications<ocnotifs>`
 * :ref:`Item Notifications<item_notifs>`

Argument Format
--------------
This documentation will also include descriptions and other details about Tornium's slash commands. The below will list how the slash command's arguments will be documented here.

.. list-table::
    :header-rows: 1

    * - Syntax
      - Definition
    * - (arg_name)
      - required argument
    * - [arg_name]
      - optional argument

API Key Usage
-------------
Depending on the slash command, Tornium will either use the faction AA API keys or the server administrators' API keys. However for most commands, if you're signed into Tornium, the bot will give preference to your API key over any other applicable keys to minimize usage on those keys.
