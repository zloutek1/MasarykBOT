# MasarykBOT

Create a bot account fllowing [this guide](https://discordpy.readthedocs.io/en/latest/discord.html).

Clone the repo:
```
git clone https://gitlab.com/zloutek1/MasarykBOT.git
cd MasarykBOT/bot/
```

## Setup database

Install a MySQL server:
- for example download [WAMP](http://www.wampserver.com/en/), LAMP or XAMPP Apache servers
- then upgrade the default MySQL 5 to MySQL 8.0+ from [mysql.com/downloads](https://dev.mysql.com/downloads/mysql/)
- to have the same database structure as the bot uses import `assets/database_setup.sql` into your database

MasarykBOT will run also without the database, but ceratin commands will be unavailable

## Setup enviroment variables

you need to setup your enviroment variables
either create a `*.env*` file.

.env file content:
```
DB_DATABASE = "discord"
DB_HOST = "localhost"
DB_PASS = "<your_password>"
DB_PORT = 3306
DB_USER = "root"
PREFIX = "!"
TOKEN = "<your_bot_token>"
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
