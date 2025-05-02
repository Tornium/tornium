# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- Added `/user` slash command
- Added field to retaliation embed for whether the original attack is a retaliation
- Added `v2` API support to `tasks.api.tornget`
- Added revivable members slash command `/faction members revivable`
- Added Elixir-based Discord gateway through Nostrum
- Added new verification on-join
- Added client-side caching to `tornium-estimate.user.js`
- Added support for advanced search to `tornium-estimate.user.js`
- Added new Lua+Solid based notification infrasture
- Added Oban and ObanWeb to Elixir worker
- Added OC delay notifications
- Added OC missing tool notifications
- Added revivable member ping slash command `/faction members revivable-ping`

### Changed
- Re-enabled Discord-based authentication
- Updated assists to utilize the DB instead of Redis as the datastore
- Changed chain alert minimum length from 100 to 250 hits
- Changed chain list generation API route from `GET /api/v1/set` to `GET /api/v1/chain-list` to avoid uBlock Origin privacy filter
- Changed Git hook tooling to Lefthook from pre-commit
- Changed `tornium-estimate.user.js` to cache `GET /api/v1/user/estimate/<tid>`
- Changed existing theme SCSS system to be better structured
- Changed `tasks.user.update_user` to update the user only if there is not data for the day
- Changed `PersonalStats` model to store per-day data instead of per-hour data
- Changed license of stat estimation code and model from proprietary to GPLv3
- Changed all license to GPLv3

### Fixed
- Fixed retaliations not being marked as completed and being spammed
- Fixed lack of pagination of server members and servers in `tasks.guilds.refresh_guilds`
- Fixed session state being overwritten before usage
- Fixed race condition in `/faction/banking/fulfill/<guid>`
- Fixed sort order and direction of `/faction members hospital`
- Fixed stat score calculation on gym page in `tornium-estimate.user.js`
- Fixed OD channel loader on website
- Fixed point withdrawals in `/withdraw`
- Fixed IP address logging in `AuthLog`

### Removed
- Removed `ddtrace` importing and setting of user ID in span within `@app.before_request`
- Removed `discord-gateway` from monorepo
- Removed verification on join from Celery worker
- Removed stakeouts
- Removed assists from Celery, application, etc.
- Removed `TorniumExt` plugin system
- Removed private user data from `GET /api/v1/user`
- Removed member personal stat report
