# MasarykBOT - Discord bot for FI MUNI server

## About

Discord bot created to enhance, monitor and manage the experience on FI MUNI discord server.

## Installation

Prerequirements:
- [python 3.7](https://www.python.org/downloads/)
- [discord.py](https://discordpy.readthedocs.io/en/latest/intro.html#installing)
- [aiomysql](https://github.com/aio-libs/aiomysql)

## Docker setup

Install `docker` and `docker-compose` for your system

you might have to run
```
sudo systemctl start docker # and/or
sudo service docker start
```

On Windows 10 you must have WSL 2 installed (build number `>= 18917`)

Once all that is ready clone the repo:
```
git clone https://gitlab.com/zloutek1/MasarykBOT.git
cd MasarykBOT/
docker-compose build
docker-compose down && docker-compose up
```
