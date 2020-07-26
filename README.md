<img align="right" src="https://cdn.discordapp.com/avatars/605352263040630795/a2205b2834e12560d416b56ec2aece06.webp?size=128" height="128" width="128">

# MasarykBOT

Discord bot created mainly for the community of Faculty of Informatics, Masaryk's university.

![Discord](https://discordapp.com/api/guilds/486184376544002073/widget.png?style=shield) ![Deploy](https://github.com/zloutek1/MasarykBOT/workflows/Deploy/badge.svg)

⁣

## Requirements

- [Python 3.8](https://www.python.org/downloads/)

- [Git](https://git-scm.com/downloads)
- [Postgresql 9.6.17](https://git-scm.com/downloads)



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
POSTGRES=postgres://user:pass@host:port/database?option=value
TOKEN=your-token
```

3. build docker
```
docker build . -t bot
```

4. run docker-compose
```
docker-compose down && docker-compose up --build
```



## Manually (optional)

1. clone this git repository
```
git clone https://github.com/zloutek1/MasarykBOT.git
cd MasarykBOT
```

2. set the environment variables
```
POSTGRES=postgres://user:pass@host:port/database?option=value
TOKEN=your-token
SNEKBOX=http://127.0.0.1:8060/eval
```

3. install python dependencies
```
python -m pip install -r requirements.txt
```

3. run bot
```
python __main__.py
```
