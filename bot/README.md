# MasarykBOT

If you want an automatized docker setup go level higher.
If you want a manual setup then continue.

## Manual setup

Clone the repo:
```
git clone https://gitlab.com/zloutek1/MasarykBOT.git
cd MasarykBOT/bot/
```

Install a MySQL server:
- for example download WAMP, LAMP or XAMPP Apache servers
- or just MySQL 8.0+

Prerequirements:
- [python 3.7](https://www.python.org/downloads/)
- [discord.py](https://discordpy.readthedocs.io/en/latest/intro.html#installing)
- [aiomysql](https://github.com/aio-libs/aiomysql)

Install python packages:
```
python3 -m pip install -r requirements.txt
```

Run the bot:
```
python3 __main__.py
```
