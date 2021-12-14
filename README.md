<img align="right" src="https://cdn.discordapp.com/avatars/605352263040630795/a2205b2834e12560d416b56ec2aece06.webp?size=128" height="128" width="128">

# MasarykBOT

Discord bot created mainly for the community of Faculty of Informatics, Masaryk's university.

![Discord](https://discordapp.com/api/guilds/486184376544002073/widget.png?style=shield) ![Deploy](https://github.com/zloutek1/MasarykBOT/workflows/Deploy/badge.svg)
⁣
## Features and commands

**Subjects**
- users are able to "sign up" for subjects that are on Masaryk's university. When enough people sign up for one subject a chat room is created where they can discuss that subjects topics.
- this is useful to declutter the discord server and find students with similar subjects.
- this also solves a problem where discord allows only 500 channels per server, allowing only the subjects with enough interest to be created.

**Leaderboard**
- user messages are counted and parsed for used emojis and reactions, which are then stored into a leaderboard table ranking the users on the amount sent
- this is a fun tool to compare and track the activity on the server with later potential applications for interesting analysis

**Eval**
- users are able to evalueate their code in languages such as `python3`, `haskell`, `C` and more
- this uses an external API as internal evaluation was little unsecure and therefore hard to implement.

**Rolemenu**
- similar to **Subjects** users are able to react on certain messages and obtain a role which then shows certain channels
- they function in a similar way, but **Rolemenu** is not dependant on a database

**Verification**
- a simple reaction check upon entering the server that forces the user to "agree to Terms and conditions"
- this feature might be removed later on as Discord has provided a build-in feature working in similar fashion.

**Other**
- features above and rest of the features can be found in `/bot/cogs` directory

## Requirements

- [Python 3.8](https://www.python.org/downloads/)

- [Git](https://git-scm.com/downloads)
- [Postgresql 9.12](https://git-scm.com/downloads)



## Heroku (recommended)

 [![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/zloutek1/MasarykBOT/tree/v2)

1. Sign up for a free account on https://www.heroku.com/
2. Create an app by clicking the Deploy to Heroku button
3. Fork this git repository
4. Go to your app at https://dashboard.heroku.com/apps
5. Click on your heroku profile > Account settings and copy the API Key
5. Go to your git repository go to settings > secrets and create two keys `HEROKU_API_KEY` and `HEROKU_APP_NAME`
5. Back in Heroku select *Deploy* tab > Deployment method: git > Enable automatic deploys
6. Then select *Resources* tab > toggle the switch on the `python ./__main__.py` Dyno
8. to see the progress you can go to *Activity* tab on Heroku to see the build process and *More > View logs* to see the stdout of the bot



## Docker (optional)

1. clone this git repository
```
git clone https://github.com/zloutek1/MasarykBOT.git
cd MasarykBOT
```

2. set the environment variables
```
# .env

POSTGRES=postgresql://masaryk:localdbpassword@database/discord
TOKEN=your-token
```

3. build docker
```
docker build . -t bot
```

4. to run the bot alone run
```
docker-compose down && docker-compose up --build bot
```

5. to run the bot with a local database run
```
docker-compose down && docker-compose up --build bot database database_backup
```

6. to only test the application run
```
docker-compose down && docker-compose up --build tests
```


## Manually (optional)

1. clone this git repository
```
git clone https://github.com/zloutek1/MasarykBOT.git
cd MasarykBOT
```

2. set the environment variables
```
POSTGRES=postgresql://masaryk:localdbpassword@database/discord
TOKEN=your-token
```

3. install python dependencies
```
python -m pip install -r requirements.txt
```

3. run bot
```
python __main__.py
```

## Links

- [Development GitHub repository](https://github.com/zloutek1/MasarykBOT)
- [FI MUNI Discord invite](https://discord.gg/fimuni)
