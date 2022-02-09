# Tornium
[Tornium](https://torn.deek.sh) is a website and Discord bot for [Torn City](https://torn.com) that supports features such as faction vault withdrawals and server stakeouts. Checkout [Features](#features) for more information.

## Major Features
 - Faction Vault Withdrawals
 - Server Stakeouts of Users and Factions
 - Chain List Generator
 - Stat DB (from faction attacks)

## Installation
Tornium can either be installed as a development server, as a production server, or as a hosted version.
Please note that Tornium has only been tested on Ubuntu 20 LTS, nginx, and uwsgi. Additionally, the frontend has only been tested with Firefox 91 and 92 (Chromium yet to be tested).
Docker containers not yet available.
If you have any questions, suggestions, or bugs to be reported, please contact tiksan [2383326] on [Discord](https://discordapp.com/users/695828257949352028) or on [Torn](https://www.torn.com/profiles.php?XID=2383326).

### Installation - Hosted Version
The hosted version of Tornium does not allow for custom bots, customization of features, etc. Please first login to [Tornium](https://torn.deek.sh/login) then proceed to the [bot hosting documentation](https://torn.deek.sh/bot/host) for more information on setting up the Discord bot. The webserver does not require any additional setup.

### Installation - Custom Server
1. Clone the project - `git clone https://github.com/dssecret/tornium.git`
2. `sudo apt-get update && sudo apt-get upgrade`
3. Install required system level packages (python3, pip3, redis-server, mongodb)
4. Create [virtual environment](https://linoxide.com/how-to-create-python-virtual-environment-on-ubuntu-20-04/) and activate virtual environment (Optional)
5. Install required Python packages - `pip3 install -r requirements.txt`
6. Set up necessary other files such as systemd, supervisord, et al.
7. Launch Redis, Huey, and MongoDB
8. Launch bot and web server


## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change or contact the developer on [Discord](https://discordapp.com/users/695828257949352028).

## License
[GNU Affero General Public License v3.0](https://github.com/dssecret/tornium/blob/master/LICENSE)
