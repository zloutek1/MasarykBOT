# MasarykBOT

Create a bot account following [this guide](https://discordpy.readthedocs.io/en/latest/discord.html).

Clone the repo:
```
git clone https://github.com/zloutek1/MasarykBOT.git
cd MasarykBOT
```

⁣

## Running

Step 1

Make sure you have [python 3.8](https://www.python.org/downloads/)

⁣

Step 2

Install python dependencies:

```
pip install -U -r requirements.txt
```

⁣

Step 3

Download and install [postgresql](https://www.postgresql.org/download/), then create the tables by importing the schemes from the [./sql/](sql/) directory.

⁣

Step 4

Setup your environment variables by creating a `.env` file.

```
POSTGRES = 'postgresql://<user>:<pass>@<server>/<database>'
TOKEN = "<your-token>"
```

⁣

## Requirements

- Python 3.8+
- v1.0.0 of discord.py
- asyncpg

⁣

## (Optional) Deployment to Heroku

- Fork this git repository
- Create an account and login to [Heroku dashboard](https://dashboard.heroku.com/apps)
- Go to new > Create a new app
- After the setup go to Deploy tab, select deployment method github, and connect to your forked github project
- Then go to Settings tab, click on Reveal Config Vars and enter your .env variables
- After all that push to git or in Deploy tab and click Deploy Branch

⁣
