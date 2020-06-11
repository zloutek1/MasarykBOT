# MasarykBOT

Create a bot account fllowing [this guide](https://discordpy.readthedocs.io/en/latest/discord.html).

Clone the repo:
```
git clone https://github.com/zloutek1/MasarykBOT.git
cd MasarykBOT
```

## Setup database

Install a MariaDB server:
- for example download [WAMP](http://www.wampserver.com/en/), LAMP or XAMPP Apache servers
- use MariaDB 10.1 so upgrade to this version if needed
- to have the same database structure as the bot uses import `assets/database_setup.sql` into your database

MasarykBOT will run also without the database, but ceratin commands will be unavailable

## Setup enviroment variables

you need to setup your enviroment variables
either create a `.env` file.

.env file content:
```
PREFIX=!
TOKEN=<your-token>

DB_HOST=<your-ip>
DB_PORT=3306
DB_USER=devMasaryk
DB_PASS=devBotOnMUNI
DB_DATABASE=discord

NEED_REACTIONS=4
```

## Python settings

Prerequirements:
- [python 3.7](https://www.python.org/downloads/)
- [discord.py](https://discordpy.readthedocs.io/en/latest/intro.html#installing)
- [aiomysql](https://github.com/aio-libs/aiomysql)

Install python packages:
```
python3 -m pip install -U -r requirements.txt
```

Run the bot:
```
python3 __main__.py
```

## (Optional) Deployment to Heroku

- Fork this git repository
- Create an account and login to [Heroku dashboard](https://dashboard.heroku.com/apps)
- Go to new > Create a new app
- After the setup go to Deploy tab, select deployment method github, and connect to your forked github project
- Then go to Settings tab, click on Reveal Config Vars and enter your .env variables
- After all that push to git or in Deploy tab and click Deploy Branch
