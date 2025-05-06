# Setup Verification
In this tutorial, we will be setting up verification in a Discord server. Verification will allow for the identification of Discord server members as Torn users. Once a user is verified on the [official Torn Discord server](https://www.torn.com/discord), Tornium will be able to identify the user's Torn account and modify the user's nickname and roles in the Discord server according to the server's configuration. Before starting, you will need to have done the following steps:
1. [Bot installation](discord-server-installation.md): Install the bot in your Discord server
2. (Optional) [Faction-server linking](discord-server-link.md): Link your faction and Discord server together

***NOTE:*** Due to Discord's permission system, Tornium is unable to verify the Discord server owner or any member of the server with a role higher than the bot's highest role. Verification of these members will have be performed manually by a server administrator.

First, we will open the Discord server's verification dashboard. Select your Discord server on Tornium's [server selector](https://tornium.com/bot/dashboard) to open your server's dashboard. Then the verification dashboard can be found under the `Verification` header of the server dashboard by pressing the `Go To Verification Settings` button. This verification dashboard contains all the configuration options for verifying members of your Discord server.

All parts of this tutorial are optional after this point. Different features can be used to configure your Discord server in different ways. For more in-depth information on verification, visit the [verification reference](../reference/bot-verification.md) page. Once your Discord server's verification is configured, you can enable verification with the [global verification toggle](../reference/bot-verification.md#global-toggle) found at the top of the server's verification dashboard.

## Minimal Verification Configuration
Now that you're on the Discord server's verification dashboard, we can start configuring the common, minimal configuration for verification: roles for verified members and roles for faction members.

First, we will be setting the roles given to members of the Discord server who are verified under `Verified Roles`. In this section, you can select multiple (or none) roles to be assigned to these members. You can ensure that the settings have saved by refreshing the page and checking the roles are still listed.

Now, we can set up roles to be assigned to members of the Discord server who are in certain factions. Under the `Faction Verification` section, there is an input box named `Torn Faction ID`. Here you can enter the [ID of the faction(s)]() for which Tornium should assign roles and then press the `Add` button next to the input. This will create a card under the `Faction Verification` section titled with the faction ID you've just entered. You can assign the roles to be assigned to Discord server members in this faction on the input within this card. Once again, you can refresh the page once adding the roles to ensure that the settings have been saved properly.

At this point, we have now set up roles to be assigned to members of your Discord server who are verified and in certain factions. Many Discord server consider this to be sufficient.

## Slash Commands
Once you've completed the minimal verification configuration, you can start using the two slash commands provided by Tornium to verify the members of the Discord server. First, you should ensure the global toggle for verification has been enabled, found at the top of the verification dashboard of the Discord server, to allow for verification of server members.

The [`/verify`](../reference/bot-verification.md#verify-command) slash command allows server members to verify themselves. By including a mention of another member, `/verify member:@Chedburn` will verify another member.

The [`/verifyall`](../reference/bot-verification.md#verify-all-command) slash command is intended for server administrators to verify all members of the Discord server. This can take a few minutes to occur, especially on larger servers.

## Daily Verification
Tornium supports verifying all members of the Discord server at a pre-determined time every day. Before we start, ensure you are on the verification dashboard for the Discord server. If you haven't already, you will need to set up at least the [minimal verification configuration](#minimal-verification-configuration) above.

First, it is recommended but not essential to enable the Discord [log channel](../reference/bot-verification.md#log-channel). The log channel can be found at the top of the verification dashboard for the Discord server under the `Basic Verification Configuration` section. This channel should be set to a channel in the Discord server restricted to server administrators. Once this log channel is set, messages regarding successful/failed verification of server members during the daily verification will be sent here.

Now, you will need to enable the feature by pressing the `Enable` button for daily verification under the `Automatic Verification` section on the verification dashboard. In the text above this button, you can also find the time daily verification will run on your Discord server.

At this point, we have set up daily verification of server members which will run automatically at the pre-determined time every day.

## Verification-on-Join
Tornium supports automatically verifying members of the Discord server as they join the server. Before we start, ensure you are on the verification dashboard for the Discord server. If you haven't already, you will need to set up at least the [minimal verification configuration](#minimal-verification-configuration) above.

First, it is recommended but not required to set up a channel members will first see as they join the Discord server -- known as the "[jail channel](../reference/bot-verification.md#jail-channel)". This will also be the channel used in the Discord invitation and is typically a channel at the top of the Discord server. The jail channel can be found at the top of the verification dashboard for the Discord server under the `Basic Verification Configuration` section. Once the jail channel for the Discord server is set, messages regarding successful/failed verification and verification instructions will be sent in this channel as members join the Discord server.

Now, you will need to enable the feature by pressing the `Enable` button for verification-on-join under the `Automatic Verification` section on the verification dashboard.

At this point, new members joining the Discord server will automatically be verified.

## More Configuration
There are further configuration options that provide more customization for verification of Discord server members on Tornium including [customizable nicknames](../reference/bot-verification.md#name-template). For more information, see the [verification reference](../reference/bot-verification.md) page.
