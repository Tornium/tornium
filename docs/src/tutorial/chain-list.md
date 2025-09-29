# Generating a Chain List
In this tutorial, we will be generating a chain list: a list of targets fulfilling certain criteria defined by you. These targets can be used to hit certain respect targets while your faction is chaining. Before generating a chain list, you will need to have one of the following:

1. You should have signed into Tornium with an API key. You can do this through the [login page](https://tornium.com/login).
2. OR... You should be in a faction where a leader has provided the stats for faction members. You can check this on the [faction members](https://tornium.com/faction/members) page under your username. If you have a "battlescore", you're good to go. Otherwise, you'll need to do option #1.

**WARNING:** The chain list generator may provide out-of-date data, especially for active players.

First, we will need to configure the chain list generator to determine which types of targets will be provided. Tornium supports the following configuration options:

- Difficulty range: The range in [fair fight](https://wiki.torn.com/wiki/Chain#Fair_fights) the targets should give you when attacked. The higher the fair fight (3x is the maximum in-game), the higher the respect the target will give and the more difficult the attack will be.
- Level range: The range in levels the targets should be. The higher the level, the higher the respect the target will give.
- Sort by: The order in which targets are generated.
- Limit: The maximum number of targets provided.
- Inactive only: Only targets that should be inactive will be provided.
- Factionless only: Only targets that should not be in the faction will be provided.

Now that the chain list generator has been configured, we can press the `Generate Chain List` button. After a few seconds, the chain list will be loaded into a series of "cards" on mobile devices and a table on desktop devices. By clicking on the targets' name, the target's profile on Torn will be opened in a new tab. The generated chain list will also provide the fair fight and respect the target should provide if attacked.

For more information on the chain list generator, see the [chain list generator reference](../reference/stats-chain-list-generator.md) page.
