# Chain List Generator
The chain list generator pulls users from Tornium's [stat database](https://tornium.com/stats/db) and filters the users to determine which users may be good chain targets providing good respect. The configuration users provide help limit the generated targets to those that will be useful to the user.

## Configuration Options
The chain list generator supports the following configurations:
- [Difficulty Range](#difficulty-range): The range in fair fight the targets should provide.
- [Level Range](#level-range): The range in levels the targets should be within.
- [Sort Order](#sort-order): The order the database will list the targets in.
- [Limit](#limit): The maximum number of targets that will be returned.
- [Inactive Only](#inactive-only): Only targets that should be inactive for more than 30 days.
- [Factionless Only](#factionless-only): Only targets that should not be in a faction.

The difficulty range, level, and limit configuration options support custom values. Adding a custom value can be done by removing the existing value from the input, typing out a new value, and pressing "Add". See the sections for each configuration option for more information on how this works for each configuration option.

**NOTE:** If the `Inactive Only` and/or `Factionless Only` filters are used, then an additional filter is utilized to prevent stale data from being included. Depending on the difference between the target's last activity in Tornium's database and last update to Tornium's database, there will be a maximum staleness of the data of between 27 and 90 days.

### Difficulty Range
The difficulty range is the range of fair fight targets will be generated for.

### Level Range
The level range is the range of targets' level for which targets will be generated for. The level must be between 1 and 100.

### Sort Order
The order targets are sorted by the database when generated.

- `Recently Updated`: Targets will be sorted by the most recently updated stat data for targets.
- `Highest Respect`: Targets will be sorted by the highest respect if they were to be attacked. This is based on the user's most recent stat score and the target's most recent stat score and level.
- `Random`: Targets will be sorted randomly.

### Limit
The maximum number of targets when the chain list is generated. The limit must be between 1 and 250.

### Inactive Only
The generated list of chain targets will only contain targets who *should* be inactive. The targets will be last active more than 30 days ago according to the database and the targets will have been updated less than 21 days ago. This ensures the target's last action timestamp has been updated sufficiently recently.

### Factionless Only
The generated list of chain targets will only contain targets who *should* not be in a faction.
