# Banking
Tornium's banking allows faction members to request money and faction bankers to fulfill/cancel vault requests. Once a vault request is marked as fulfilled, the banker needs to be fulfilled within ten minutes; without a vault log indicating the vault request has been fulfilled, the bot will mark the vault request as not fulfilled and cancel it. By default, if a vault request is not fulfilled within ~60 minutes, the bot will automatically cancel the request in an attempt to prevent the requester of the vault request from being mugged after going offline. This can be configured by the member making the request though.

## Banking Configuration
Under the `Faction Banking` section of the faction's linked Discord server, the faction's banking channel and optional role(s) can be configured. The banking channel is the location vault requests will be sent to. If the optional banking role(s) are configured, the roles will be mentioned in the request sent to the banking channel.

## Slash Commands
Tornium's Discord bot contains four banking-related slash commands:
- [`/balance`](#balance-command): Command to check a member's balance
- [`/withdraw`](#withdraw-command): Command to perform a vault request 
- [`/cancel`](#cancel-command): Command to cancel a vault request
- [`/fulfill`](#fulfill-command): Command to fulfill a vault request

### Balance Command
```
/balance [member]
```

The `/balance` slash command will attempt to retrieve the user's faction vault balance for their current faction. This command requires a member of their faction with [AA permissions](faction-aa.md) to be signed in Tornium.

If this slash command is invoked in a Discord server and the invoker of the command has [AA permissions](faction-aa.md) in their faction, a Discord user can be included to retrieve that other user's vault balance if both users are in the same faction.

| Argument | Description                                  | Required | Default                |
| -------- | -------------------------------------------- | -------- | ---------------------- |
| `member` | Discord server member to retrieve balance of | False    | Invoker of the command |

### Withdraw Command
```
/withdraw (amount) [option]
```

The `/withdraw` slash command will send a vault request for the specified amount of money or points to the banking channel mentioning the banking role as configured for the faction of the invoker. Before sending the vault request to the banking channel, the bot will verify the member has a sufficient balance of money or points in the faction vault. Additionally, the member can not have pending requests of which the balance would go over the member's balance with the request being made.

| Argument  | Description                                     | Required | Default |
| --------- | ----------------------------------------------- | -------- | ------- |
| `amount`  | Amount of money/points to be withdrawn          | True     | None    |
| `option`  | Flag to request money or points to be withdrawn | False    | Money   |
| `timeout` | Amount of time before the request will time out | False    | 1 hour  |


The `(amount)` parameter allows for the suffixes used by Torn for ease-of-use as shown below (e.g. `4.3m` represents `4,300,000`). Additionally, `all` can be used in place of a numeric amount to request all of the member's vault balance.

| Suffix | Amount        |
| ------ | ------------- |
| 1K     | 1,000         |
| 1M     | 1,000,000     |
| 1B     | 1,000,000,000 |

### Cancel Command
```
/cancel [id]
```

The `/cancel` slash command will cancel a vault request. If no vault request ID is provided, the most recent vault request by the user will be cancelled. If a vault request ID is provided and the user has [AA permissions](faction-aa.md), the specified vault request will be cancelled.

| Argument | Description                      | Required | Default                   |
| -------- | -------------------------------- | -------- | ------------------------- |
| `id`     | Vault request ID to be cancelled | False    | Most recent vault request |


### Fulfill Command
```
/fulfill (id)
```

The `/fulfill` slash command will mark a vault request as fulfilled by the command invoker.

| Argument | Description                      | Required | Default |
| -------- | -------------------------------- | -------- | ------- |
| `id`     | Vault request ID to be fulfilled | True     | None    |


## Website
In addition to the above slash commands, faction members can make vault requests and view previous vault requests through the [Tornium website](https://tornium.com/faction/banking). At the top of this page, members can input the amount (of only money) to withdraw and submit the request; this process works the same as the [`/withdraw`](#withdraw-command) slash command. Below this, members can view a list of faction bankers and a list of their previous vault requests.

