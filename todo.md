## Needs to be done
 - Migrate certain sections of the bot admin dashboard to use the channel selector
### Frontend
 - Update faction documentation
 - Update stat DB documentation
### Backend
 - Add stakeouts to DB after Discord, Torn, and DB calls are made
### SkyNet
 - Add helper function to handle Torn (and possible Discord) API call errors
 - Implement stat DB commands
 - Add value-based faction armory usage to stakeouts
 - Update stakeout embeds
### API
 - Fix some API calls returning ratelimit and HTTP status in body instead of header
 - Update all bot API calls to use the same format: /api/bot/<int:guildid>/
### Low Priority
 - Add additional log messages for automated actions and flask/Discord-based actions that modify the database
 - Fix styling of certain sections (primarily comma use)
 - Create Tornium API documentation
 - Add docstrings to util funcs