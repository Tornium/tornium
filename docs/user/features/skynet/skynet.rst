.. _skynet

SkyNet
===============
SkyNet is Tornium's latest Discord bot module built from scratch using the Discord API preventing other packages from influencing the long-term stability of SkyNet.

Inviting the Bot
----------------
Only members that have the server administrator permission will be allowed to set up the server.

You can invite SkyNet onto your server with either specific, required permissions or administrator permissions. The former is preferred for privacy/security reasons, but the latter will be easier to set up for most server administrators. However, unlike previous Discord bots, SkyNet relies entirely upon slash commands to call a command so the bot will be unable to read any messages posted in your servers.

 * Required permissions invite link: `<https://discord.com/api/oauth2/authorize?client_id=979105784627593266&permissions=469969968&scope=bot%20applications.commands>`_
 * Administrator permissions invite link: `<https://discord.com/api/oauth2/authorize?client_id=979105784627593266&permissions=8&scope=bot%20applications.commands>`_

Bot Modules
-----------
Almost all of the bot's configuration will be done through the bot dashboard found on the `Tornium website <https://tornium.com/bot/dashboard>`_ but many user-oriented features can be found on the bot.

 * :ref:`Verification<verification>`
 * :ref:`Faction Banking<banking>`
 * :ref:`Assists<assists>`
 * :ref:`Retaliations<retals>`
 * :ref:`Organized Crime Notifications<ocnotifs>`
 * :ref:`Stakeouts<stakeouts>`

Argument Format
--------------
This documentation will also include descriptions and other details about SkyNet's slash commands. The below will list how the slash command's arguments will be documented here.

.. list-table::
    :header-rows: 1

    * - Syntax
      - Definition
    * - arg_name
      - required argument
    * - [arg_name]
      - optional argument

API Key Usage
-------------
Depending on the slash command, Tornium will either use the faction AA API keys or the server administrators' API keys. However for most commands, if you're signed into Tornium, the bot will give preference to your API key over any other applicable keys to minimize usage on those keys.
