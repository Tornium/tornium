## Done
 - Finish /user/who command

## Requires Internet
 - Install Mongo, Redis, and required packages **ASAP**
 - Fix force option type for bot/verify/verify and bot/verify/verifyall (requires API connection for Discord docs)

## Needs to be done
 - Migrate certain sections of the bot admin dashboard to use the channel selector
 - Create JS and Py util funcs (for both frontend and backend usage) to streamline channel selector
 - OC delay via bot with settings via bot admin dashboard
### Frontend
### Backend
### Bot
 - Create helper function for the listing of admins/API keys regardless of call invocation location
 - Add helper function to handle Torn (and possible Discord) API call errors
 - Implement stat DB commands
### API
 - Improve Tornium API error codes (most are code 0 rn)
### Low Priority
 - Add additional log messages for automated actions and flask/Discord-based actions that modify the database
 - Fix styling of certain sections (primarily comma use)
 - Add release notes w/ GH releases
 - Create Tornium API documentation
 - Add docstrings to util funcs