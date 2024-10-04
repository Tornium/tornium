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

### Changed
- Re-enabled Discord-based authentication
- Updated assists to utilize the DB instead of Redis as the datastore
- Changed chain alert minimum length from 100 to 250 hits
- Changed chain list generation API route from `GET /api/v1/set` to `GET /api/v1/chain-list` to avoid uBlock Origin privacy filter
- Changed Git hook tooling to Lefthook from pre-commit

### Fixed
- Fixed retaliations not being marked as completed and being spammed
- Fixed lack of pagination of server members and servers in `tasks.guilds.refresh_guilds`
- Fixed session state being overwritten before usage

### Removed
- Removed `ddtrace` importing and setting of user ID in span within `@app.before_request`
- Removed `discord-gateway` from monorepo
- Removed verification on join from Celery worker
- Removed assists from Celery, application, etc.
