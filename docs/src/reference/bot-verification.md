# Bot Verification
Tornium's Discord member verification updates a Discord member's roles and nickname according to the server's verification configuration and the member's Discord ID. The verification feature requires a Discord server's member to be verified through the [official Torn Discord server](https://torn.com/discord) to determine which Torn user corresponds to a Discord user.

***NOTE:*** Due to restrictions with Discord’s permission system, Tornium is unable to modify the nicknames and roles of server members with a role higher than the bot’s highest role or modify the server owner. Changes to these members need to be done manually by a server administrator. Server owners are considered to be the highest role in the server by Discord, so the bot will never be able to verify the server owner.

## Verification Configuration
To customize your server's verification process, Tornium has several options that can be configured:
- [Global toggle](#global-toggle): Global toggle enabling/disabling verification
- [Log channel](#log-channel): Discord channel verification-logs are sent to
- [Jail channel](#jail-channel): Discord channel un-verified server members should be restricted to 
- [Cron Toggle](#verification-cron-toggle): Toggle enabling/disabling daily verification
- [On-Join Toggle](#verification-on-join-toggle): Toggle enabling/disabling verification on member join
- [Name template](#name-template): Template for verified members' nicknames
- [Exclusion roles](#exclusion-roles): Roles of members that won't be verified
- [Faction roles](#faction-roles): Roles assigned to members of specified factions
- [Faction position roles](#faction-position-roles): Roles assigned to members who have specific faction positions

These configuration options can be set on the Tornium website on the verification dashboard for any Discord server the Tornium bot is in. For basic information on setting up verification in a Discord server, the [tutorial](../tutorial/discord-server-verification.md) is recommended.

### Global Toggle
The verification global toggle enables or disables all [verification methods](#verification-methods) for that Discord server. The global toggle does not delete any saved configurations which allows verification to be later enabled without any further configuration.

### Log Channel
All verification log messages will be sent to the specified verification log channel or thread in the Discord server. Currently, only successful/failed changes to members during [`/verifyall`]() and the [verification cron](verification-cron) will be logged to this channel.

### Jail Channel
All un-verified members who have joined the server are intended to arrive through this channel or thread. If the Discord server has [verification-on-join](verification-on-join) enabled, the bot will send messages regarding successful/unsuccessful verification in the jail channel. If the member is not verified through Torn, the bot will indicate methods for the member to verify themselves.

### Verification Cron Toggle
The verification cron toggle will enable/disable automated daily verification of all members in the Discord server. For more information, see [verification-cron](#verification-cron).

### Verification-on-Join Toggle
The verification-on-join toggle will enable/disable verification of new members when they join the Discord server. For more information, see [verification-on-join](verification-on-join).

### Name Template
The verification name template is used to generate the nickname for all members in the Discord server. By default, the template is `{{ name }} [{{ tid }}]` such that the nickname of [Chedburn](https://www.torn.com/profiles.php?XID=1) would be `Chedburn [1]`. However, this can be customized with the name template at runtime through certain Jinja-like variables:

| Variable   | Description             | Example    |
| ---------- | ----------------------- | ---------- |
| {{ name }} | Torn username           | `Chedburn` |
| {{ tid }}  | Torn user ID            | `1`        |
| {{ tag }}  | Torn user's faction tag | `CR`       |

### Exclusion Roles
All members in the Discord server who have an exclusion role will not be verified through any [verification method](#verification-methods). These members will have to have their nickname and roles be manually updated by a server administrator. Exclusion roles are commonly used to allow faction members who are guesting to retain faction-related roles and to skip verification of server administrators.

### Faction Roles
Members of the Discord server can be given role(s) corresponding to their faction in-game. If the member is not in a faction configured for verification in the Discord server, there will be no faction-related changes during verification. The factions configured for faction roles during verification do not have to be [linked](../tutorial/discord-server-link.md) to the Discord server.

### Faction Position Roles
Members of the Discord server can be given role(s) corresponding to their faction positions for their faction in-game. Assigning roles to faction positions requires adding the faction to the list of factions the Discord server will verify, but [faction roles](#faction-roles) are not required to set up this feature.

This feature requires configured factions to maintain a link between the configured faction and the Discord server. Additionally, to avoid leaking potentially sensitive data, only members of that faction with the faction's [AA permission](../reference/faction-aa.md) will be able to configure this feature.

## Verification Methods
To perform the verification of Discord server members, Tornium supports three options:
- [Verification-on-join](#verification-on-join): New members of the Discord server will be verified upon joining the server
- [Verification cron](#verification-cron): All members of the Discord server will be verified daily
- [Slash commands](#slash-commands): Members of the Discord server can be verified through a series of slash commands

### Verification-on-Join
Verification-on-join utilizes the Discord gateway to verify new members of the Discord server as they join. Upon detecting the member joining the Discord server, the bot will attempt to verify the member according to the Discord server's verification configuration. If the verification configuration has [verification-on-join disabled](#verification-on-join-toggle), no verification (including API calls) will be performed.

Once verification is complete, if a [jail channel](#jail-channel) is configured, the bot will send a message regarding the success of verification to the jail channel. It is assumed that the jail channel is where new members land as the bot's message includes instructions on how the member can verify for members who are not already verified.

### Verification Cron
The verification cron will attempt to verify all members of the Discord server if enabled through the [cron toggle](#verification-cron-toggle). The verification cron occurs at a time calculated from the Discord server's ID which can be found on the verification dashboard under `Automatic Verification`. At that time, the cron will start to verify all members of the Discord server. This process can take several minutes depending on load on Tornium's servers, the number of members of the Discord server, and the number of API keys to be used. As the verification process progresses, messages regarding the success of verification for individual members will be sent to the configured [log channel](#log-channel).

***NOTE:*** Larger Discord servers will need to have multiple API keys to process verification in a timely manner. The Torn API ratelimits API calls per key owner and, to avoid using all of a user's ratelimit, Tornium only utilizes a portion of that ratelimit.

## Slash Commands
Tornium's Discord bot contains two slash commands related to performing verification:
- [`/verify`](#verify-command): Command to verify yourself or another member
- [`/verifyall`](#verify-all-command): Command to manually start verification cron

### Verify Command
```
/verify [member] [force]
```

The `/verify` slash command will attempt to verify a member of the Discord server according to the Discord server's verification configuration.

| Argument | Description                                   | Required | Default                |
| -------- | --------------------------------------------- | -------- | ---------------------- |
| `member` | Discord server member to be verified          | False    | Invoker of the command |
| `force`  | Flag to require updated data on the Torn user | False    | True                   |

### Verify All Command
```
/verifyall [force]
```

The `/verifyall` slash command will manually start the [verification cron](#verification-cron) to verify all members of the Discord server in the background. This verification process can take up to several minutes. For more information, see the [verification cron](#verification-cron).

| Argument | Description                                   | Required | Default |
| -------- | --------------------------------------------- | -------- | ------- |
| `force`  | Flag to require updated data on the Torn user | False    | True    |

