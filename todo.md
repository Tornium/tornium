## Requires Internet
 - Fix some links and add data in user/who SkyNet command

## Needs to be done
 - Migrate certain sections of the bot admin dashboard to use the channel selector
 - Create JS and Py util funcs (for both frontend and backend usage) to streamline channel selector
 - OC delay via bot with settings via bot admin dashboard
 - Redo bot admin dashboard server selector (primarily DB-related)
### Frontend
 - Update faction documentation
 - Update bot documentation
 - Update stat DB documentation
### Backend
 - Add stakeouts to DB after Discord, Torn, and DB calls are made
### SkyNet
 - Add helper function to handle Torn (and possible Discord) API call errors
 - Implement stat DB commands
 - Add OC ready and delay watchers
 - Add value-based faction armory usage to stakeouts
### API
 - Improve Tornium API error codes (most are code 0 rn)
 - Fix some API calls returning ratelimit and HTTP status in body instead of header
### Low Priority
 - Add additional log messages for automated actions and flask/Discord-based actions that modify the database
 - Fix styling of certain sections (primarily comma use)
 - Create Tornium API documentation
 - Add docstrings to util funcs